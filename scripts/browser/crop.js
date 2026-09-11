// Screenshot one element at 2x. Usage: node crop.js <url> <selector> <out.png> [width]
const { chromium } = require('playwright');
const [url, selector, out, width] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(width || 1280), height: 900 }, deviceScaleFactor: 2 });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);
  const el = await page.$(selector);
  if (!el) { console.log('no element for', selector); process.exit(1); }
  await el.screenshot({ path: out });
  // THE BOX, IN CSS PX FROM THE PAGE'S TOP-LEFT, SINCE 2026-09-11 -- so an
  // alignment question ("is the button centred on the title's first line?",
  // "is the nav on the cards' edge?") is answered by two numbers rather than by
  // squinting at two images. getBoundingClientRect plus the scroll offset.
  const box = await el.evaluate((node) => {
    const r = node.getBoundingClientRect();
    const f = (n) => Math.round(n * 10) / 10;
    return { x: f(r.left + window.scrollX), y: f(r.top + window.scrollY), w: f(r.width), h: f(r.height) };
  });
  console.log('wrote', out, `box x=${box.x} y=${box.y} w=${box.w} h=${box.h} right=${Math.round((box.x + box.w) * 10) / 10}`);
  await browser.close();
})();
