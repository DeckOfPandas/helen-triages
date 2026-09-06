// =============================================================================
// Tests for what the index scripts ASK OF filter-state.js — issue #633.
//
// Run from tests/js with `node --test`.
//
// WHAT WENT WRONG, AND WHY EVERY EXISTING TEST STAYED GREEN. On 2026-08-31
// cocktail-index.js read `FilterState.arrivedByGoingBack` — which is on the
// filter-state MODULE and not on the binding `create(SPEC)` returns. That is
// `undefined`, calling undefined throws, and so THE ENTIRE TAIL OF THE FILE
// STOPPED RUNNING: the back/forward restore, `apply()` at startup (the index
// stopped applying its own filters and its shuffle), and the `pagehide`
// listener that saves the list.
//
// Every JS test stayed green, and that is the point of #633 rather than a
// detail of that bug. All of them ask a pure module a question and get a
// correct answer; the fault was in the WIRING BETWEEN two modules, which is the
// one place a suite of pure-function tests cannot look.
//
// THE TRAP IS THAT ONE NAME MEANS TWO OBJECTS:
//
//   filters.js          var FilterState = HTF.filterState;              the MODULE
//   cocktail-index.js   var FilterState = HTF.filterState.create(...);  a BINDING
//
// Same variable, same-looking property access, two different surfaces. Nothing
// but this notices.
//
// THIS IS NOT ALL OF #633 AND DOES NOT CLAIM TO BE. The issue asks for the
// index scripts to be RUN, which needs a DOM these scripts can start against;
// that is a real piece of work and is still open. This covers the specific
// class of fault that issue was raised from, statically, for the price of a
// file — and it would have failed on the 2026-08-31 revision.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

const JS_DIR = path.join(__dirname, '..', '..', 'assets', 'js');
const FS_MODULE = require(path.join(JS_DIR, 'filter-state.js'));

function source(name) {
  return fs.readFileSync(path.join(JS_DIR, name), 'utf8');
}

// Strip comments before scanning for property access. Both files discuss
// `FilterState.arrivedByGoingBack` in prose — cocktail-index.js's own comment is
// the record of the bug — and a scanner that read those would report the fault
// as still present for ever.
function code(text) {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, ' ')
    .replace(/(^|[^:])\/\/[^\n]*/g, '$1 ');
}

/* What `var <name> = ...` is bound to: the module, or a create() binding. */
function bindingKind(text, name) {
  const re = new RegExp('var\\s+' + name + '\\s*=\\s*([^;]+);');
  const m = re.exec(code(text));
  if (!m) return null;
  return /\.create\s*\(/.test(m[1]) ? 'binding' : 'module';
}

function propertiesUsed(text, name) {
  const used = new Set();
  const re = new RegExp('\\b' + name + '\\.([A-Za-z_$][\\w$]*)', 'g');
  let m;
  while ((m = re.exec(code(text))) !== null) used.add(m[1]);
  return used;
}

const SCRIPTS = [
  { file: 'cocktail-index.js', spec: 'COCKTAIL_FIELDS' },
  { file: 'filters.js', spec: 'FOOD_FIELDS' }
];

test('filter-state exposes a module and a binding, and they differ', () => {
  // If these ever became the same object the trap would be gone -- and so would
  // the reason for every test below. Asserting it makes that a decision.
  const binding = FS_MODULE.create(FS_MODULE.COCKTAIL_FIELDS);
  assert.ok(FS_MODULE.arrivedByGoingBack, 'the module lost arrivedByGoingBack');
  assert.strictEqual(
    binding.arrivedByGoingBack, undefined,
    'a create() binding now carries arrivedByGoingBack. If that was deliberate, ' +
    'the 2026-08-31 bug is no longer possible and #633 can say so.'
  );
});

for (const { file, spec } of SCRIPTS) {
  test(`${file} only asks its FilterState for things that object has`, () => {
    const text = source(file);
    const kind = bindingKind(text, 'FilterState');
    assert.ok(
      kind,
      `${file} no longer declares \`var FilterState = ...\`. This test found it ` +
      `by that name; if it was renamed, rename it here too rather than deleting ` +
      `the check.`
    );

    const target = kind === 'binding'
      ? FS_MODULE.create(FS_MODULE[spec])
      : FS_MODULE;

    const available = new Set(Object.keys(target));
    const missing = [...propertiesUsed(text, 'FilterState')]
      .filter((p) => !available.has(p))
      .sort();

    assert.deepStrictEqual(
      missing, [],
      `${file} reads these off its FilterState (${kind}) and they are not on ` +
      `it, so each is \`undefined\` at runtime:\n  ${missing.join('\n  ')}\n\n` +
      `This is issue #633's bug exactly. The module and a create() binding are ` +
      `different objects with different surfaces, and calling an undefined one ` +
      `throws — which stops the REST OF THE FILE, not just that line.`
    );
  });

  test(`${file} only asks HTF.filterState for things the module has`, () => {
    const text = source(file);
    const available = new Set(Object.keys(FS_MODULE));
    const missing = [...propertiesUsed(text, 'HTF.filterState')]
      .filter((p) => !available.has(p))
      .sort();
    assert.deepStrictEqual(
      missing, [],
      `${file} reads these straight off HTF.filterState and the module does ` +
      `not export them:\n  ${missing.join('\n  ')}`
    );
  });
}

test('the scanner ignores property names that only appear in comments', () => {
  // cocktail-index.js's own comment names `FilterState.arrivedByGoingBack` as
  // the thing that broke. If this scanner read comments it would report that
  // bug as permanently present, the test would be permanently red, and the
  // first thing anybody did would be to delete it.
  const withComment = `
    /* FilterState.arrivedByGoingBack is undefined -- see #633. */
    var FilterState = HTF.filterState.create(SPEC);
    // FilterState.neverRealEither
    FilterState.emptyState();
  `;
  const used = propertiesUsed(withComment, 'FilterState');
  assert.ok(used.has('emptyState'), 'the scanner missed a real call.');
  assert.ok(!used.has('arrivedByGoingBack'), 'a block comment was scanned.');
  assert.ok(!used.has('neverRealEither'), 'a line comment was scanned.');
});

test('the scanner can tell a binding from the module', () => {
  assert.strictEqual(
    bindingKind('var FilterState = HTF.filterState;', 'FilterState'), 'module');
  assert.strictEqual(
    bindingKind('var FilterState = HTF.filterState.create(HTF.filterState.COCKTAIL_FIELDS);',
      'FilterState'), 'binding');
});

test('the guard fires on the 2026-08-31 source, not just passes on today\'s', () => {
  // The bug as it was written: FilterState is a create() binding, and
  // arrivedByGoingBack is read off it. Reconstructed rather than checked out,
  // so this test needs no git history to stay meaningful.
  const broken = `
    var FilterState = HTF.filterState.create(HTF.filterState.COCKTAIL_FIELDS);
    var state = FilterState.emptyState();
    var arrivedByGoingBack = FilterState.arrivedByGoingBack;
  `;
  const kind = bindingKind(broken, 'FilterState');
  assert.strictEqual(kind, 'binding');

  const target = FS_MODULE.create(FS_MODULE.COCKTAIL_FIELDS);
  const available = new Set(Object.keys(target));
  const missing = [...propertiesUsed(broken, 'FilterState')]
    .filter((p) => !available.has(p));

  assert.deepStrictEqual(
    missing, ['arrivedByGoingBack'],
    'the guard did not report the very property whose absence stopped the ' +
    'whole file running. A guard that cannot fail its own worked example is ' +
    'not protecting anything.'
  );

  // And the fixed form -- reading it off the module -- is clean.
  const fixed = broken.replace(
    'FilterState.arrivedByGoingBack', 'HTF.filterState.arrivedByGoingBack');
  const stillMissing = [...propertiesUsed(fixed, 'FilterState')]
    .filter((p) => !available.has(p));
  assert.deepStrictEqual(stillMissing, []);
});
