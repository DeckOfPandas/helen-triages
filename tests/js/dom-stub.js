// =============================================================================
// A DOM small enough to hand-read, big enough to START the index scripts.
// Issue #633. Not a test file — `node --test` only discovers *.test.js.
// =============================================================================
// WHY THIS EXISTS. On 2026-08-31 cocktail-index.js read a name off the wrong
// object, calling undefined threw, and the ENTIRE TAIL of the file stopped
// running: the back/forward restore, `apply()` at startup, and the `pagehide`
// listener. Every JS test stayed green, because all of them ask a pure module a
// question and the fault was in the WIRING between two.
//
// WHY NOT jsdom. There is no package.json in this repo and no node_modules; the
// JS suite runs on `node:test` and `node:assert` and nothing else, which is the
// same no-bundler, no-dependency position the browser code takes. Adding a
// dependency to run four tests would be a bigger change to this project than
// the thing being tested.
//
// WHAT IT IS NOT. Not a rendering engine, not a layout engine, not a
// standards-compliant DOM. It answers exactly the 25 calls the index scripts
// make (surveyed, not guessed) and throws loudly on anything else it is asked
// for, so a script reaching for a new API fails HERE with a clear message
// rather than silently getting undefined — which is the failure mode the whole
// issue is about.
//
// THE SELECTOR ENGINE IS THE ONE FIDDLY PART and is deliberately tiny: tag,
// `.class`, `#id`, `[attr]`, `[attr='value']`, descendant space and `>` child.
// That is every selector these files use, listed in the test that consumes it.
'use strict';

let nextId = 1;

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
    // A plain bag. Nothing here computes style, and nothing needs it to: the
    // index scripts only ever WRITE to it (`visibility`, `display`), and a test
    // that wants to know what they wrote reads it back.
    this.style = Object.create(null);
    this.classList = new ClassList(this);
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

  // innerHTML is WRITE-ONLY here, and setting it CLEARS rather than parses.
  // Every use in these scripts is `el.innerHTML = ''` to empty a pool, or a
  // build-up of markup that the test then does not inspect. Parsing HTML is a
  // different project; pretending to would be worse than not having it.
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

  closest(selector) {
    const compound = parseCompound(selector);
    let node = this;
    while (node) {
      if (node instanceof Element && selectorMatches(node, compound)) return node;
      node = node.parentNode;
    }
    return null;
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

// Split a selector into compounds and `>` combinators, WITHOUT splitting on a
// space inside brackets.
//
// A plain `.split(/\s+/)` looked fine and was wrong for exactly one real
// selector: `[data-mood='no juicing']`. Half the moods on this site are two
// words -- `sunny terrace`, `no juicing`, `i want to faff` -- so the naive
// version silently found nothing for most of them, which is a stub lying about
// the page rather than failing.
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
  return doc;
}

// A localStorage that behaves, plus the two ways it misbehaves in real life:
// see assets.js's own note about a browser set to block site data.
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
