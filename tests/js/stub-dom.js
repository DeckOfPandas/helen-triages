// The stub-page harness: running a browser-only script under `node --test`.
// Not a test file (no `.test.js`), so the runner does not try to run it.
//
// `assets/js/assets.js` is the first script every page loads; it reads two
// <meta> tags at parse time and attaches to `window.HTF` rather than
// exporting, so requiring it from Node throws on `window`. The page is stubbed
// instead (MANUAL §10.2): build a fake `window`/`document`, `vm.runInContext`
// the shipped source into it, and read what it attached.
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const REPO_ROOT = path.resolve(__dirname, '..', '..');

/**
 * A minimal page: enough `document` for a script to read its two meta tags,
 * and a `console` that keeps warnings out of the test output while still
 * recording them, so a test can assert one happened.
 *
 * `window` IS the sandbox, as it is in a browser, so a script may reach a
 * global either bare (`sessionStorage.getItem`) or through `window`
 * (`window.scrollY`) and get the same object both ways.
 *
 * @param {Object} [metas] - meta tag name -> content, e.g. {'base-url': '/x/'}
 * @returns {Object} the contextified sandbox
 */
function makePage(metas) {
  const tags = metas || { 'base-url': '/', 'site-key': 'food' };
  const warnings = [];
  const sandbox = {
    document: {
      querySelector(selector) {
        const match = /^meta\[name="([^"]+)"\]$/.exec(selector);
        if (!match) return null;
        const content = tags[match[1]];
        if (content === undefined) return null;
        return { getAttribute: () => content };
      }
    },
    console: {
      warn: (message) => warnings.push(message),
      log: () => {},
      error: (message) => warnings.push(message)
    },
    fetch: () => { throw new Error('the stub page makes no network calls'); },
    warnings
  };
  sandbox.window = sandbox;
  return vm.createContext(sandbox);
}

/**
 * Run repo scripts into a stub page, in the order the built page loads them,
 * and hand back the page. Read that order from the built site, not from a
 * layout: a layout's own scripts land inside `{{ content }}` and are not
 * where the file suggests (MANUAL §10.2).
 *
 * @param {string[]} relPaths - repo-root-relative, e.g. ['assets/js/assets.js']
 * @param {Object} [page] - an existing page from makePage(), or a fresh one
 * @returns {Object} the page, with whatever the scripts attached to it
 */
function load(relPaths, page) {
  const context = page || makePage();
  relPaths.forEach((relPath) => {
    const file = path.join(REPO_ROOT, relPath);
    vm.runInContext(fs.readFileSync(file, 'utf8'), context, { filename: file });
  });
  return context;
}

/** The common case: assets.js alone, returning its HTF namespace. */
function loadHTF(page) {
  return load(['assets/js/assets.js'], page).HTF;
}

module.exports = { makePage, load, loadHTF, REPO_ROOT };
