// Screenshot pages of a running site, full page, at narrow-phone (360),
// phone (390) and desktop (1280) widths. 360 is the narrowest phone in common
// use, and where a layout that fits 390 most often starts to scroll sideways.
//
// USAGE:
//   node tools/dev/shoot.js <base-url> <label> [--engine chromium|webkit] [--scheme light|dark] [--click <text>]... [--type <text>] <page>...
//
//   node tools/dev/shoot.js http://127.0.0.1:9000/mysite before --scheme dark . about/
//   node tools/dev/shoot.js http://127.0.0.1:9000 safari --engine webkit .
//   node tools/dev/shoot.js http://127.0.0.1:9000 menu --click "Menu" .
//   node tools/dev/shoot.js http://127.0.0.1:9000 typed --type search-term .
//
// A page is relative to the base URL, and `.` is the base itself. A page
// may not start with `/`: the permission checker reads such an argument as
// an absolute file path and stops the command to ask.
//
// Shots land in tmp/shots/<label>-<width>-<scheme>-<page>.png, with
// -webkit after the width for WebKit, the engine nearest Safari. Each --click
// clicks the first visible element with that exact text, in order, before the
// shot; --type then types its text into the first visible text or search
// input. Tall pages come out tall: tools/dev/slice-png.js cuts them into
// readable pieces.
//
// Each shot's line says `ok`, or `OVERFLOW` when the page is wider than the
// viewport (sideways scrolling on a phone), followed by the elements that
// stick out furthest.
//
// Needs WITH_PLAYWRIGHT=1 in kit.env. The image sets NODE_PATH to
// /opt/playwright/node_modules, so `require('playwright')` resolves with no
// prefix on the command.
const fs = require('fs');
const path = require('path');

const WIDTHS = { narrow: 360, phone: 390, desktop: 1280 };
const OUT_DIR = 'tmp/shots';

function parse(argv) {
  const [base, label, ...rest] = argv;
  if (!base || !label) usage('give a base URL and a label');
  const opts = { base: base.replace(/\/$/, ''), label, scheme: 'light', engine: 'chromium', clicks: [], type: null, paths: [] };
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === '--engine') {
      opts.engine = rest[++i];
      if (!['chromium', 'webkit'].includes(opts.engine)) usage(`--engine is chromium or webkit, not '${opts.engine}'`);
    } else if (rest[i] === '--scheme') {
      opts.scheme = rest[++i];
      if (!['light', 'dark'].includes(opts.scheme)) usage(`--scheme is light or dark, not '${opts.scheme}'`);
    } else if (rest[i] === '--click') {
      if (rest[i + 1] === undefined) usage('--click needs the text to click');
      opts.clicks.push(rest[++i]);
    } else if (rest[i] === '--type') {
      if (rest[i + 1] === undefined) usage('--type needs the text to type');
      opts.type = rest[++i];
    } else if (rest[i].startsWith('/')) {
      usage(`'${rest[i]}' must be relative to the base URL, with no leading /: '${rest[i].replace(/^\/+/, '') || '.'}'`);
    } else {
      opts.paths.push(rest[i] === '.' ? '' : rest[i]);
    }
  }
  if (!/^[A-Za-z0-9._-]+$/.test(label)) usage(`'${label}' must be letters, digits, . _ -`);
  if (opts.paths.length === 0) opts.paths.push('');
  return opts;
}

// Runs in the page. Mobile emulation grows the layout viewport to fit the
// widest content, so innerWidth would hide the overflow: the width asked for
// is the yardstick. Names the elements that stick out furthest, widest first.
function overflow(width) {
  const docW = Math.max(document.documentElement.scrollWidth, window.innerWidth);
  if (docW <= width) return { docW, wide: [] };
  const wide = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && (r.right > width + 1 || r.left < -1)) {
      const cls = typeof el.className === 'string' ? el.className.slice(0, 60) : '';
      wide.push({ tag: el.tagName.toLowerCase(), cls, left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width) });
    }
  }
  wide.sort((a, b) => b.right - a.right);
  return { docW, wide: wide.slice(0, 8) };
}

function usage(message) {
  console.error(`shoot.js: ${message}\nusage: node tools/dev/shoot.js <base-url> <label> [--engine chromium|webkit] [--scheme light|dark] [--click <text>]... [--type <text>] <page>...`);
  process.exit(2);
}

(async () => {
  const opts = parse(process.argv.slice(2));
  // Required after the arguments are checked, so a usage error needs no browser.
  const engine = require('playwright')[opts.engine];
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await engine.launch();
  const tag = opts.engine === 'chromium' ? '' : `-${opts.engine}`;
  let failed = false;
  for (const [name, width] of Object.entries(WIDTHS)) {
    const context = await browser.newContext({
      viewport: { width, height: 900 }, colorScheme: opts.scheme,
      isMobile: name !== 'desktop', hasTouch: name !== 'desktop', deviceScaleFactor: name === 'desktop' ? 1 : 2,
    });
    const page = await context.newPage();
    for (const p of opts.paths) {
      const slug = p.replace(/\/$/, '').replace(/[^A-Za-z0-9._-]+/g, '_') || 'root';
      const file = path.join(OUT_DIR, `${opts.label}-${name}${tag}-${opts.scheme}-${slug}.png`);
      try {
        await page.goto(opts.base + '/' + p, { waitUntil: 'networkidle' });
        for (const text of opts.clicks) {
          await page.getByText(text, { exact: true }).locator('visible=true').first().click();
          await page.waitForTimeout(200);
        }
        if (opts.type !== null) {
          const box = page.locator('input[type="search"], input[type="text"], input:not([type])').locator('visible=true').first();
          await box.click();
          await box.pressSequentially(opts.type, { delay: 20 });
          await page.waitForTimeout(400);
        }
        await page.waitForTimeout(300);
        const report = await page.evaluate(overflow, width);
        await page.screenshot({ path: file, fullPage: true });
        const flag = report.docW > width ? `OVERFLOW doc=${report.docW} viewport=${width}` : 'ok';
        console.log(`${name} ${p} ${flag} -> ${file}`);
        for (const w of report.wide) {
          console.log(`    <${w.tag} class="${w.cls}"> left=${w.left} right=${w.right} width=${w.width}`);
        }
      } catch (e) {
        failed = true;
        console.log(`${name} ${p} ERROR ${e.message.split('\n')[0]}`);
      }
    }
    await context.close();
  }
  await browser.close();
  process.exit(failed ? 1 : 0);
})();
