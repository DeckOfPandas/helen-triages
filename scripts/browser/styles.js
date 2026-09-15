// Print, for every element matching a selector, its box (CSS px) and a set
// of computed styles.
// Usage: node styles.js <url> <selector> <width> <props-csv-or-empty>
const { chromium } = require('playwright');
const [url, selector, width, propsArg] = process.argv.slice(2);

const DEFAULT_PROPS = [
  'font-family', 'font-size', 'font-weight', 'line-height', 'letter-spacing',
  'text-transform', 'color', 'background-color',
  'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
  'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
  'gap', 'display',
];
const props = propsArg ? propsArg.split(',') : DEFAULT_PROPS;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(width || 1280), height: 900 } });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(300);
  const els = await page.$$(selector);
  if (!els.length) { console.log('no elements for', selector); process.exit(1); }
  for (let i = 0; i < els.length; i++) {
    const data = await els[i].evaluate((node, props) => {
      const r = node.getBoundingClientRect();
      const f = (n) => Math.round(n * 10) / 10;
      const cs = getComputedStyle(node);
      const styles = {};
      for (const p of props) styles[p] = cs.getPropertyValue(p);
      return {
        x: f(r.left + window.scrollX), y: f(r.top + window.scrollY),
        w: f(r.width), h: f(r.height), right: f(r.left + window.scrollX + r.width),
        styles,
      };
    }, props);
    console.log(`[${i}] <${selector}> box x=${data.x} y=${data.y} w=${data.w} h=${data.h} right=${data.right}`);
    for (const p of props) console.log(`    ${p}: ${data.styles[p]}`);
  }
  await browser.close();
})();
