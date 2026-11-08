// Print, for every element matching a selector on a running site, its box in
// CSS px from the page's top-left and a set of computed styles. Writes nothing.
//
// USAGE:
//   node tools/dev/styles.js <base-url> <selector> [<page>] [--width <px>] [--engine chromium|webkit] [--props a,b,c]
//
//   node tools/dev/styles.js http://127.0.0.1:9000 h1
//   node tools/dev/styles.js http://127.0.0.1:9000 '.card p' about/ --width 390 --props font-size,line-height
//
// <page> is relative to the base URL (`.` by default) and may not start with
// `/`: the permission checker reads that as an absolute path and asks. Without
// --props it prints type, colour, margins, padding, gap and display.
//
// Needs WITH_PLAYWRIGHT=1 in kit.env (see tools/dev/shoot.js).
const DEFAULT_PROPS = [
  'font-family', 'font-size', 'font-weight', 'line-height', 'letter-spacing',
  'text-transform', 'color', 'background-color',
  'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
  'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
  'gap', 'display',
];
const USAGE = 'usage: node tools/dev/styles.js <base-url> <selector> [<page>] [--width <px>] [--engine chromium|webkit] [--props a,b,c]';

function usage(message) {
  console.error(`styles.js: ${message}\n${USAGE}`);
  process.exit(2);
}

function parse(argv) {
  const [base, selector, ...rest] = argv;
  if (!base || !selector) usage('give a base URL and a selector');
  const opts = { base: base.replace(/\/$/, ''), selector, page: '', width: 1280, engine: 'chromium', props: DEFAULT_PROPS };
  let gotPage = false;
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === '--width') {
      opts.width = Number(rest[++i]);
      if (!Number.isInteger(opts.width) || opts.width < 200 || opts.width > 4000) usage('--width must be a whole number from 200 to 4000');
    } else if (rest[i] === '--engine') {
      opts.engine = rest[++i];
      if (!['chromium', 'webkit'].includes(opts.engine)) usage(`--engine is chromium or webkit, not '${opts.engine}'`);
    } else if (rest[i] === '--props') {
      const list = rest[++i];
      if (!list || !/^[a-z-]+(,[a-z-]+)*$/.test(list)) usage('--props is a comma-separated list of CSS property names');
      opts.props = list.split(',');
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
  const page = await browser.newPage({ viewport: { width: opts.width, height: 900 } });
  await page.goto(opts.base + '/' + opts.page, { waitUntil: 'networkidle' });
  await page.waitForTimeout(300);
  const els = await page.$$(opts.selector);
  if (!els.length) { console.error(`styles.js: nothing matches ${opts.selector}`); await browser.close(); process.exit(1); }
  for (let i = 0; i < els.length; i++) {
    const d = await els[i].evaluate((node, props) => {
      const r = node.getBoundingClientRect();
      const f = (n) => Math.round(n * 10) / 10;
      const cs = getComputedStyle(node);
      const styles = {};
      for (const p of props) styles[p] = cs.getPropertyValue(p);
      return { x: f(r.left + window.scrollX), y: f(r.top + window.scrollY), w: f(r.width), h: f(r.height), styles };
    }, opts.props);
    console.log(`[${i}] ${opts.selector} box x=${d.x} y=${d.y} w=${d.w} h=${d.h} right=${Math.round((d.x + d.w) * 10) / 10}`);
    for (const p of opts.props) console.log(`    ${p}: ${d.styles[p]}`);
  }
  await browser.close();
})();
