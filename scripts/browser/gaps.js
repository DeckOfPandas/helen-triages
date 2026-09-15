// Walk the visible block-level children under a root element (default
// `main`), printing each one's tag.class, height, margin/padding top/bottom,
// and the gap in px to the sibling before it -- an indented tree to depth 4.
// Usage: node gaps.js <url> <width> <root-selector>
const { chromium } = require('playwright');
const [url, width, rootSelector] = process.argv.slice(2);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(width || 1280), height: 900 } });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(300);
  const lines = await page.evaluate((root) => {
    const out = [];
    const round = (n) => Math.round(n * 10) / 10;

    function label(el) {
      const cls = typeof el.className === 'string' && el.className.trim()
        ? '.' + el.className.trim().split(/\s+/).join('.') : '';
      return el.tagName.toLowerCase() + cls;
    }

    function visibleBlockChildren(el) {
      const kids = [];
      for (const child of el.children) {
        const cs = getComputedStyle(child);
        if (cs.display === 'none' || cs.display === 'inline') continue;
        if (cs.position === 'absolute' || cs.position === 'fixed') continue;
        const r = child.getBoundingClientRect();
        if (r.width < 6 && r.height < 6) continue;
        kids.push(child);
      }
      return kids;
    }

    function walk(el, depth) {
      if (depth > 4) return;
      const kids = visibleBlockChildren(el);
      let prevBottom = null;
      for (const child of kids) {
        const cs = getComputedStyle(child);
        const r = child.getBoundingClientRect();
        const gap = prevBottom === null ? null : round(r.top - prevBottom);
        const indent = '  '.repeat(depth);
        const gapNote = gap === null ? '' : ` gap-before=${gap}`;
        out.push(`${indent}${label(child)} h=${round(r.height)} `
          + `margin-top=${cs.marginTop} margin-bottom=${cs.marginBottom} `
          + `padding-top=${cs.paddingTop} padding-bottom=${cs.paddingBottom}${gapNote}`);
        prevBottom = r.bottom;
        walk(child, depth + 1);
      }
    }

    const rootEl = document.querySelector(root);
    if (!rootEl) return [`no element for ${root}`];
    walk(rootEl, 0);
    return out.length ? out : [`no visible block children under ${root}`];
  }, rootSelector || 'main');
  console.log(lines.join('\n'));
  await browser.close();
})();
