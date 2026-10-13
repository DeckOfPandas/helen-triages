// Screenshot one element at 2x.
// Usage: node crop.js <url> <selector> <out.png> [width] [type-into-selector] [text]
//
// The last two arguments type into a box before the shot (#1050): a dropdown
// that opens as you type cannot be seen on a page nobody has typed into. The
// box is focused, the text typed key by key, and the shot waits for the
// network to go quiet (the search box fetches its index on first focus) and
// then a beat for the paint.
const { chromium } = require('playwright');
const [url, selector, out, width, typeInto, text] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(width || 1280), height: 900 }, deviceScaleFactor: 2 });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);
  if (typeInto) {
    const box = await page.$(typeInto);
    if (!box) { console.log('no element to type into for', typeInto); process.exit(1); }
    await box.focus();
    await page.waitForLoadState('networkidle');
    await box.type(text || '', { delay: 40 });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);
  }
  const el = await page.$(selector);
  if (!el) { console.log('no element for', selector); process.exit(1); }
  await el.screenshot({ path: out });
  // The box, in CSS px from the page's top-left, so an alignment question is
  // answered by two numbers. getBoundingClientRect plus the scroll offset.
  const box = await el.evaluate((node) => {
    const r = node.getBoundingClientRect();
    const f = (n) => Math.round(n * 10) / 10;
    return { x: f(r.left + window.scrollX), y: f(r.top + window.scrollY), w: f(r.width), h: f(r.height) };
  });
  console.log('wrote', out, `box x=${box.x} y=${box.y} w=${box.w} h=${box.h} right=${Math.round((box.x + box.w) * 10) / 10}`);
  await browser.close();
})();
