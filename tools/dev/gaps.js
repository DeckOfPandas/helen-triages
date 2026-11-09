// Print the vertical rhythm under one element: each visible block child's
// tag.class, height, margins and padding, and the gap in px to the sibling
// above it, as an indented tree. Writes nothing.
//   node tools/dev/gaps.js <base-url> <root-selector> [<page>] [--width <px>] [--depth <n>] [--engine chromium|webkit]
//   node tools/dev/gaps.js http://127.0.0.1:9000 .card about/ --width 390 --depth 2
// <page> is relative to the base URL (`.` by default) and never starts with
// `/` (see shoot.js). Skipped: absolute and fixed children, `display: none`,
// inline elements and anything under 6x6 px. --depth is 1 to 8, default 4.
// Needs WITH_PLAYWRIGHT=1 in kit.env.
const USAGE = 'usage: node tools/dev/gaps.js <base-url> <root-selector> [<page>] [--width <px>] [--depth <n>] [--engine chromium|webkit]';

function usage(message) {
  console.error(`gaps.js: ${message}\n${USAGE}`);
  process.exit(2);
}

function parse(argv) {
  const [base, root, ...rest] = argv;
  if (!base || !root) usage('give a base URL and a root selector');
  const opts = { base: base.replace(/\/$/, ''), root, page: '', width: 1280, depth: 4, engine: 'chromium' };
  let gotPage = false;
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === '--width') {
      opts.width = Number(rest[++i]);
      if (!Number.isInteger(opts.width) || opts.width < 200 || opts.width > 4000) usage('--width must be a whole number from 200 to 4000');
    } else if (rest[i] === '--depth') {
      opts.depth = Number(rest[++i]);
      if (!Number.isInteger(opts.depth) || opts.depth < 1 || opts.depth > 8) usage('--depth must be a whole number from 1 to 8');
    } else if (rest[i] === '--engine') {
      opts.engine = rest[++i];
      if (!['chromium', 'webkit'].includes(opts.engine)) usage(`--engine is chromium or webkit, not '${opts.engine}'`);
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

// Runs in the page.
function tree({ root, depth: maxDepth }) {
  const out = [];
  const round = (n) => Math.round(n * 10) / 10;
  const label = (el) => {
    const cls = typeof el.className === 'string' && el.className.trim()
      ? '.' + el.className.trim().split(/\s+/).join('.') : '';
    return el.tagName.toLowerCase() + cls;
  };
  const blockChildren = (el) => [...el.children].filter((child) => {
    const cs = getComputedStyle(child);
    if (cs.display === 'none' || cs.display === 'inline') return false;
    if (cs.position === 'absolute' || cs.position === 'fixed') return false;
    const r = child.getBoundingClientRect();
    return r.width >= 6 || r.height >= 6;
  });
  const walk = (el, depth) => {
    if (depth >= maxDepth) return;
    let prevBottom = null;
    for (const child of blockChildren(el)) {
      const cs = getComputedStyle(child);
      const r = child.getBoundingClientRect();
      const gap = prevBottom === null ? '' : ` gap-before=${round(r.top - prevBottom)}`;
      out.push(`${'  '.repeat(depth)}${label(child)} h=${round(r.height)} `
        + `margin=${cs.marginTop}/${cs.marginBottom} padding=${cs.paddingTop}/${cs.paddingBottom}${gap}`);
      prevBottom = r.bottom;
      walk(child, depth + 1);
    }
  };
  const rootEl = document.querySelector(root);
  if (!rootEl) return null;
  walk(rootEl, 0);
  return out;
}

(async () => {
  const opts = parse(process.argv.slice(2));
  // Required after the arguments are checked, so a usage error needs no browser.
  const browser = await require('playwright')[opts.engine].launch();
  const page = await browser.newPage({ viewport: { width: opts.width, height: 900 } });
  await page.goto(opts.base + '/' + opts.page, { waitUntil: 'networkidle' });
  await page.waitForTimeout(300);
  const lines = await page.evaluate(tree, { root: opts.root, depth: opts.depth });
  await browser.close();
  if (lines === null) { console.error(`gaps.js: nothing matches ${opts.root}`); process.exit(1); }
  console.log(lines.length ? lines.join('\n') : `no visible block children under ${opts.root}`);
})();
