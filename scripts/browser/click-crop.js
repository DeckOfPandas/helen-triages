// Click the first match of one selector, then screenshot another element at
// 2x -- for a control that only reveals or changes something once clicked.
// Usage: node click-crop.js <url> <click-selector> <crop-selector> <out.png> [width]
const { chromium } = require('playwright');
const [url, clickSelector, cropSelector, out, width] = process.argv.slice(2);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(width || 1280), height: 900 }, deviceScaleFactor: 2 });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);

  const clickEl = await page.$(clickSelector);
  if (!clickEl) { console.log('no element to click for', clickSelector); process.exit(1); }
  await clickEl.click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(400);

  const el = await page.$(cropSelector);
  if (!el) { console.log('no element for', cropSelector); process.exit(1); }
  await el.screenshot({ path: out });
  // THE BOX, IN CSS PX FROM THE PAGE'S TOP-LEFT, as crop.js prints it.
  const box = await el.evaluate((node) => {
    const r = node.getBoundingClientRect();
    const f = (n) => Math.round(n * 10) / 10;
    return { x: f(r.left + window.scrollX), y: f(r.top + window.scrollY), w: f(r.width), h: f(r.height) };
  });
  console.log('wrote', out, `box x=${box.x} y=${box.y} w=${box.w} h=${box.h} right=${Math.round((box.x + box.w) * 10) / 10}`);
  await browser.close();
})();
