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
  console.log('wrote', out);
  await browser.close();
})();
