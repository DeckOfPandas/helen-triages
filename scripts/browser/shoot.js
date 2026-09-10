// Screenshot a list of built pages at phone and desktop widths, and report any
// page whose document is wider than its viewport, naming the widest elements.
// Usage: node tmp/browser/shoot.js <base-url> <out-dir> <label> <path>...
const { chromium } = require('playwright');
const path = require('path');

const [base, outDir, label, ...paths] = process.argv.slice(2);
const VIEWPORTS = {
  phone: { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  narrow: { width: 360, height: 780, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  desktop: { width: 1280, height: 900, deviceScaleFactor: 1 },
};

(async () => {
  const browser = await chromium.launch();
  for (const [vpName, vp] of Object.entries(VIEWPORTS)) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: vp.deviceScaleFactor, isMobile: !!vp.isMobile, hasTouch: !!vp.hasTouch });
    const page = await context.newPage();
    for (const p of paths) {
      const url = base + p;
      const slug = p.replace(/^\/|\/$/g, '').replace(/\//g, '_') || 'root';
      try {
        await page.goto(url, { waitUntil: 'networkidle' });
        await page.waitForTimeout(300);
        const report = await page.evaluate((expected) => {
          // Mobile emulation grows the layout viewport to fit the widest
          // content, so innerWidth is the SYMPTOM; compare against what a real
          // phone has, which is the width we asked for.
          const vw = expected;
          const docW = Math.max(document.documentElement.scrollWidth, window.innerWidth);
          const wide = [];
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            if (r.width > 0 && (r.right > vw + 1 || r.left < -1)) {
              wide.push({ tag: el.tagName.toLowerCase(), cls: el.className && el.className.baseVal === undefined ? String(el.className).slice(0, 60) : '', left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width) });
            }
          }
          wide.sort((a, b) => b.right - a.right);
          return { vw, docW, wide: wide.slice(0, 8) };
        }, vp.width);
        const file = path.join(outDir, `${label}-${vpName}-${slug}.png`);
        await page.screenshot({ path: file, fullPage: true });
        const flag = report.docW > report.vw ? 'OVERFLOW' : 'ok';
        console.log(`${vpName} ${p} ${flag} doc=${report.docW} vp=${report.vw} -> ${file}`);
        if (report.docW > report.vw) {
          for (const w of report.wide) console.log(`    <${w.tag} class="${w.cls}"> left=${w.left} right=${w.right} width=${w.width}`);
        }
      } catch (e) {
        console.log(`${vpName} ${p} ERROR ${e.message.split('\n')[0]}`);
      }
    }
    await context.close();
  }
  await browser.close();
})();
