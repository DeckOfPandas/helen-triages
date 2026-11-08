// Screenshot one element of a running site at 2x, for looking closely, and
// print its box in CSS px from the page's top-left.
//
// USAGE:
//   node tools/dev/crop.js <base-url> <label> <selector> [<page>] [--width <px>] [--engine chromium|webkit] [--click <selector>] [--type-into <selector> <text>]
//
//   node tools/dev/crop.js http://127.0.0.1:9000 header .site-header
//   node tools/dev/crop.js http://127.0.0.1:9000 menu nav about/ --width 390
//   node tools/dev/crop.js http://127.0.0.1:9000 open-menu .menu-panel . --click .menu-button
//   node tools/dev/crop.js http://127.0.0.1:9000 dropdown .search-results . --type-into .search-input ch
//
// The shot lands in tmp/shots/crop-<label>.png. <page> is relative to the
// base URL (`.` by default) and may not start with `/`: the permission checker
// reads that as an absolute path and asks. --click clicks the first match for
// its selector before the shot, for a control that reveals or changes
// something. --type-into then types <text> into the first match for its
// selector, for something that only shows once somebody has typed, such as a
// search dropdown. A dropdown usually hangs outside its box, so crop the
// dropdown's own selector.
//
// Needs WITH_PLAYWRIGHT=1 in kit.env (see tools/dev/shoot.js).
const fs = require('fs');
const path = require('path');

const OUT_DIR = 'tmp/shots';
const USAGE = 'usage: node tools/dev/crop.js <base-url> <label> <selector> [<page>] [--width <px>] [--engine chromium|webkit] [--click <selector>] [--type-into <selector> <text>]';

function usage(message) {
  console.error(`crop.js: ${message}\n${USAGE}`);
  process.exit(2);
}

function parse(argv) {
  const [base, label, selector, ...rest] = argv;
  if (!base || !label || !selector) usage('give a base URL, a label and a selector');
  if (!/^[A-Za-z0-9._-]+$/.test(label)) usage(`'${label}' must be letters, digits, . _ -`);
  const opts = { base: base.replace(/\/$/, ''), label, selector, page: '', width: 1280, engine: 'chromium', click: null, typeInto: null, text: '' };
  let gotPage = false;
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === '--width') {
      opts.width = Number(rest[++i]);
      if (!Number.isInteger(opts.width) || opts.width < 200 || opts.width > 4000) usage('--width must be a whole number from 200 to 4000');
    } else if (rest[i] === '--engine') {
      opts.engine = rest[++i];
      if (!['chromium', 'webkit'].includes(opts.engine)) usage(`--engine is chromium or webkit, not '${opts.engine}'`);
    } else if (rest[i] === '--click') {
      if (rest[i + 1] === undefined) usage('--click needs a selector');
      opts.click = rest[++i];
    } else if (rest[i] === '--type-into') {
      if (rest[i + 1] === undefined || rest[i + 2] === undefined) usage('--type-into needs a selector and the text to type');
      opts.typeInto = rest[++i];
      opts.text = rest[++i];
    } else if (rest[i].startsWith('-')) {
      usage(`unknown option '${rest[i]}'`);
    } else if (gotPage) {
      usage(`one page only, got a second: '${rest[i]}'`);
    } else if (rest[i].startsWith('/')) {
      usage(`'${rest[i]}' must be relative to the base URL, with no leading /: '${rest[i].replace(/^\/+/, '') || '.'}'`);
    } else {
      opts.page = rest[i] === '.' ? '' : rest[i];
      gotPage = true;
    }
  }
  return opts;
}

(async () => {
  const opts = parse(process.argv.slice(2));
  // Required after the arguments are checked, so a usage error needs no browser.
  const browser = await require('playwright')[opts.engine].launch();
  const page = await browser.newPage({ viewport: { width: opts.width, height: 900 }, deviceScaleFactor: 2 });
  await page.goto(opts.base + '/' + opts.page, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);
  if (opts.click !== null) {
    const target = await page.$(opts.click);
    if (!target) { console.error(`crop.js: nothing matches ${opts.click}`); await browser.close(); process.exit(1); }
    await target.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);
  }
  if (opts.typeInto !== null) {
    const box = await page.$(opts.typeInto);
    if (!box) { console.error(`crop.js: nothing matches ${opts.typeInto}`); await browser.close(); process.exit(1); }
    await box.focus();
    await page.waitForLoadState('networkidle');
    await box.pressSequentially(opts.text, { delay: 40 });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);
  }
  const el = await page.$(opts.selector);
  if (!el) { console.error(`crop.js: nothing matches ${opts.selector}`); await browser.close(); process.exit(1); }
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const file = path.join(OUT_DIR, `crop-${opts.label}.png`);
  await el.screenshot({ path: file });
  const b = await el.evaluate((node) => {
    const r = node.getBoundingClientRect();
    const f = (n) => Math.round(n * 10) / 10;
    return { x: f(r.left + window.scrollX), y: f(r.top + window.scrollY), w: f(r.width), h: f(r.height) };
  });
  console.log(`${file} box x=${b.x} y=${b.y} w=${b.w} h=${b.h} right=${Math.round((b.x + b.w) * 10) / 10}`);
  await browser.close();
})();
