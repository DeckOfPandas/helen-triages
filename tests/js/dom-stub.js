// A DOM small enough to hand-read, big enough to start the index scripts
// (#633). Not a test file: `node --test` only discovers *.test.js.
//
// It exists so a fault in the wiring between two modules, which no pure-module
// test can see, stops the suite. Not jsdom: the repo has no package.json and
// the JS suite runs on `node:test` and `node:assert` alone.
//
// Not a rendering engine, a layout engine or a standards-compliant DOM: it
// answers only the calls the index scripts make.
//
// The selector engine is deliberately tiny: tag, `.class`, `#id`, `[attr]`,
// `[attr='value']`, descendant space and `>` child.
'use strict';

let nextId = 1;

/** `el.style`: a plain bag of written values, plus the CSSOM methods.
 *
 * The three methods are non-enumerable so that everything which treats this as
 * a bag -- reading `style.display`, listing what a script wrote -- is
 * unchanged. `setProperty` is the only way to write a custom property, and
 * card-line-budget.js writes `--ship-w` (#1107).
 */
function makeStyle() {
  const bag = Object.create(null);
  const method = (name, fn) =>
    Object.defineProperty(bag, name, { value: fn, enumerable: false });
  method('setProperty', (key, value) => { bag[key] = String(value); });
  method('removeProperty', (key) => { const had = bag[key]; delete bag[key]; return had; });
  method('getPropertyValue', (key) => (key in bag ? bag[key] : ''));
  return bag;
}

class ClassList {
  constructor(el) { this.el = el; }
  _list() { return this.el.className ? this.el.className.split(/\s+/).filter(Boolean) : []; }
  _set(list) { this.el.className = list.join(' '); }
  contains(name) { return this._list().indexOf(name) !== -1; }
  add(...names) {
    const l = this._list();
    names.forEach((n) => { if (l.indexOf(n) === -1) l.push(n); });
    this._set(l);
  }
  remove(...names) { this._set(this._list().filter((c) => names.indexOf(c) === -1)); }
  toggle(name, force) {
    const on = force === undefined ? !this.contains(name) : !!force;
    if (on) this.add(name); else this.remove(name);
    return on;
  }
}

class Element {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.uid = nextId++;
    this.className = '';
    this.children = [];
    this.parentNode = null;
    this.attributes = Object.create(null);
    this.dataset = Object.create(null);
    this.listeners = Object.create(null);
    this._text = '';
    this.hidden = false;
    this.value = '';
    // A plain bag: nothing here computes style. The index scripts only write
    // to it, and a test reads back what they wrote (see makeStyle).
    this.style = makeStyle();
    this.classList = new ClassList(this);

    // --- measurement ------------------------------------------------------
    // A test sets `el.__box` to the rect this element should report and
    // `el.__contentWidth` to the width a Range over its contents should give
    // (#1107). Nothing here computes layout, and nothing should: the stub has
    // no line breaking, font metrics or box model, so a computed pixel would
    // be a number this file invented.
    this.__box = null;
    this.__contentWidth = 0;
  }

  /** True unless this element or an ancestor is `hidden`.
   *
   * The index paginates by setting `card.hidden`, and a hidden element
   * measures zero in both directions in a real browser (#1115).
   */
  get __rendered() {
    for (let node = this; node; node = node.parentNode) {
      if (node.hidden) return false;
    }
    return true;
  }

  get clientWidth() {
    if (!this.__rendered || !this.__box) return 0;
    return this.__box.clientWidth || 0;
  }

  getBoundingClientRect() {
    const b = this.__rendered ? (this.__box || {}) : {};
    const width = b.width || 0;
    const height = b.height || 0;
    const top = b.top || 0;
    const left = b.left || 0;
    return {
      width, height, top, left,
      right: b.right === undefined ? left + width : b.right,
      bottom: b.bottom === undefined ? top + height : b.bottom
    };
  }

  /** `[]` for anything not laid out, one rect otherwise -- the browser's own
   *  answer to "did you get a box for this", which card-name-fit.js asks
   *  instead of checking `hidden` itself (#1115). */
  getClientRects() {
    if (!this.__rendered || !this.__box) return [];
    const rect = this.getBoundingClientRect();
    if (!rect.width && !rect.height) return [];
    return [rect];
  }

  // --- tree ---------------------------------------------------------------
  appendChild(node) {
    if (node instanceof Fragment) {
      node.children.slice().forEach((c) => this.appendChild(c));
      node.children = [];
      return node;
    }
    if (node.parentNode) node.parentNode.removeChild(node);
    node.parentNode = this;
    this.children.push(node);
    return node;
  }

  insertBefore(node, ref) {
    if (node.parentNode) node.parentNode.removeChild(node);
    const at = ref ? this.children.indexOf(ref) : -1;
    node.parentNode = this;
    if (at === -1) this.children.push(node);
    else this.children.splice(at, 0, node);
    return node;
  }

  removeChild(node) {
    const at = this.children.indexOf(node);
    if (at !== -1) this.children.splice(at, 1);
    node.parentNode = null;
    return node;
  }

  remove() { if (this.parentNode) this.parentNode.removeChild(this); }

  get firstChild() { return this.children[0] || null; }

  // --- content ------------------------------------------------------------
  get textContent() {
    if (this.children.length === 0) return this._text;
    return this.children.map((c) => c.textContent).join('');
  }

  set textContent(v) {
    this.children.forEach((c) => { c.parentNode = null; });
    this.children = [];
    this._text = String(v);
  }

  // Setting innerHTML clears rather than parses: the scripts use it to empty
  // a pool, or to build markup no test inspects.
  get innerHTML() { return this._html || ''; }
  set innerHTML(v) {
    this._html = String(v);
    this.children.forEach((c) => { c.parentNode = null; });
    this.children = [];
    this._text = '';
  }

  // --- attributes ---------------------------------------------------------
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === 'class') this.className = String(value);
    if (name.indexOf('data-') === 0) this.dataset[dashToCamel(name.slice(5))] = String(value);
  }

  getAttribute(name) {
    if (name === 'class') return this.className;
    return name in this.attributes ? this.attributes[name] : null;
  }

  hasAttribute(name) { return this.getAttribute(name) !== null; }
  removeAttribute(name) { delete this.attributes[name]; }

  // --- events -------------------------------------------------------------
  addEventListener(type, fn) {
    (this.listeners[type] = this.listeners[type] || []).push(fn);
  }

  // results-bar.js forwards its clear-all to the index's button by calling
  // click(), so a click is a dispatched click.
  click() { this.dispatch('click'); }

  // Fire a listener as the browser would, for the tests that need to click.
  dispatch(type, event) {
    const ev = Object.assign({ type: type, target: this, preventDefault() {} }, event || {});
    let node = this;
    while (node) {
      (node.listeners[type] || []).forEach((fn) => fn.call(node, ev));
      node = node.parentNode;
    }
  }

  // --- queries ------------------------------------------------------------
  querySelectorAll(selector) { return matchAll(this, selector); }
  querySelector(selector) { return matchAll(this, selector)[0] || null; }

  matches(selector) { return selectorMatches(this, parseCompound(selector)); }

  contains(other) {
    for (let node = other; node; node = node.parentNode) if (node === this) return true;
    return false;
  }

  closest(selector) {
    const compound = parseCompound(selector);
    let node = this;
    while (node) {
      if (node instanceof Element && selectorMatches(node, compound)) return node;
      node = node.parentNode;
    }
    return null;
  }

  // Recorded, never absent (#1057, #1059): filters.js and cocktail-index.js
  // feature-test `typeof el.scrollIntoView === 'function'` before calling it,
  // so without this every arrival-scroll test would pass by never running the
  // code. Tests read `_scrollCalls` back.
  scrollIntoView(opts) {
    this._scrollCalls = this._scrollCalls || [];
    this._scrollCalls.push(opts);
  }

  // Everything below this element, document order.
  _descendants(out) {
    out = out || [];
    this.children.forEach((c) => {
      if (!(c instanceof Element)) return;
      out.push(c);
      c._descendants(out);
    });
    return out;
  }
}

class TextNode {
  constructor(text) { this._text = String(text); this.parentNode = null; }
  get textContent() { return this._text; }
  set textContent(v) { this._text = String(v); }
}

class Fragment {
  constructor() { this.children = []; }
  appendChild(node) {
    if (node.parentNode) node.parentNode.removeChild(node);
    node.parentNode = null;
    this.children.push(node);
    return node;
  }
}

function dashToCamel(name) {
  return name.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
}

// --- the selector engine -----------------------------------------------------
// Splits on descendant/child combinators, then matches right-to-left the lazy
// way: find every candidate for the LAST compound, then walk back up.

function parseCompound(text) {
  const out = { tag: null, classes: [], id: null, attrs: [] };
  const re = /([.#]?[\w-]+|\[[^\]]*\])/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const t = m[1];
    if (t[0] === '.') out.classes.push(t.slice(1));
    else if (t[0] === '#') out.id = t.slice(1);
    else if (t[0] === '[') {
      const a = /\[\s*([\w-]+)\s*(?:([~|^$*]?=)\s*['"]?([^'"\]]*)['"]?)?\s*\]/.exec(t);
      if (a) out.attrs.push({ name: a[1], op: a[2] || null, value: a[3] });
    } else out.tag = t.toUpperCase();
  }
  return out;
}

function selectorMatches(el, c) {
  if (c.tag && el.tagName !== c.tag) return false;
  if (c.id && el.getAttribute('id') !== c.id) return false;
  for (const cls of c.classes) if (!el.classList.contains(cls)) return false;
  for (const a of c.attrs) {
    const got = el.getAttribute(a.name);
    if (got === null) return false;
    if (a.op === '=' && got !== a.value) return false;
  }
  return true;
}

// Split a selector into compounds and `>` combinators, without splitting on a
// space inside brackets: `[data-mood='no juicing']` is one compound, and a
// plain `.split(/\s+/)` silently finds nothing for every two-word mood.
function splitCombinators(selector) {
  const parts = [];
  let buf = '';
  let depth = 0;
  let quote = null;
  const push = () => { if (buf.trim()) parts.push(buf.trim()); buf = ''; };

  for (const ch of String(selector).trim()) {
    if (quote) {
      buf += ch;
      if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") { quote = ch; buf += ch; continue; }
    if (ch === '[') { depth++; buf += ch; continue; }
    if (ch === ']') { depth--; buf += ch; continue; }
    if (depth === 0 && /\s/.test(ch)) { push(); continue; }
    if (depth === 0 && ch === '>') { push(); parts.push('>'); continue; }
    buf += ch;
  }
  push();
  return parts;
}

function matchAll(root, selector) {
  const results = [];
  const seen = new Set();
  String(selector).split(',').forEach((one) => {
    const parts = splitCombinators(one);
    // parts is like ['.a', '>', 'li'] or ['.drink-card-name', 'a']
    const steps = [];
    for (let i = 0; i < parts.length; i++) {
      if (parts[i] === '>') { steps[steps.length - 1].child = true; continue; }
      steps.push({ compound: parseCompound(parts[i]), child: false });
    }
    if (!steps.length) return;

    const last = steps[steps.length - 1];
    root._descendants().forEach((el) => {
      if (!selectorMatches(el, last.compound)) return;
      // Walk the remaining steps upward.
      let node = el;
      let ok = true;
      for (let i = steps.length - 2; i >= 0; i--) {
        const step = steps[i];
        const mustBeParent = steps[i + 1].child;
        node = node.parentNode;
        if (mustBeParent) {
          if (!(node instanceof Element) || !selectorMatches(node, step.compound)) {
            ok = false; break;
          }
        } else {
          while (node instanceof Element && !selectorMatches(node, step.compound)) {
            node = node.parentNode;
          }
          if (!(node instanceof Element)) { ok = false; break; }
        }
      }
      if (ok && !seen.has(el.uid)) { seen.add(el.uid); results.push(el); }
    });
  });
  return results;
}

// --- the document ------------------------------------------------------------

function createDocument() {
  const doc = new Element('html');
  doc.body = new Element('body');
  doc.appendChild(doc.body);

  doc.createElement = (tag) => new Element(tag);
  doc.createTextNode = (t) => new TextNode(t);
  doc.createDocumentFragment = () => new Fragment();
  doc.getElementById = (id) => doc.querySelector('#' + id);
  doc.readyState = 'complete';
  doc.documentElement = doc;

  /* card-name-fit.js measures the lettering with a Range over the contents
     (#1107). The stub answers from the element's `__contentWidth`, and
     reports zero for anything not laid out so the hidden-card path is
     reachable. */
  doc.createRange = () => {
    let node = null;
    return {
      selectNodeContents(el) { node = el; },
      getBoundingClientRect() {
        if (!node || !node.__rendered) return { width: 0, height: 0 };
        return { width: node.__contentWidth || 0, height: 0 };
      },
      detach() {}
    };
  };
  return doc;
}

// A localStorage that behaves.
function createStorage(initial) {
  const map = new Map(Object.entries(initial || {}));
  return {
    getItem: (k) => (map.has(k) ? map.get(k) : null),
    setItem: (k, v) => { map.set(k, String(v)); },
    removeItem: (k) => { map.delete(k); },
    clear: () => map.clear(),
    get length() { return map.size; },
    key: (i) => Array.from(map.keys())[i] || null,
    _map: map
  };
}

module.exports = { Element, TextNode, Fragment, createDocument, createStorage, parseCompound, matchAll };
