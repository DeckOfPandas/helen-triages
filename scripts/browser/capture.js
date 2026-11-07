// The design-review screenshot set (#1453): every page type and every
// reachable state of both sites, at phone, iPad-portrait and desktop widths,
// as PNGs plus a manifest (index.md, shots.json) in <out-dir>.
//
//   node scripts/browser/capture.js <base-url> <out-dir> <commit>
//
// Run it through capture.sh, which serves nothing itself: it needs this
// worktree's serve.sh running. Every shot is wrapped, so a state that fails is
// recorded in the manifest with its error and the run carries on. A selector
// here that the templates rename becomes a FAILED row, not a crash.
'use strict';
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const [BASE, OUT, commit] = process.argv.slice(2);
if (!BASE || !OUT || !commit) {
  console.error('usage: node scripts/browser/capture.js <base-url> <out-dir> <commit>');
  process.exit(2);
}

const VIEWPORTS = {
  phone: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  ipad: { viewport: { width: 1024, height: 1366 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  desktop: { viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 },
};

const PAGES = {
  food: {
    index: '/food/',
    recipeFull: '/food/recipes/moules-mariniere/',
    recipe2: '/food/recipes/pineapple-ginger-spatchcock-chicken/',
    temps: '/food/reference/internal-temperatures/',
    methods: '/food/reference/cooking-methods-and-timings/',
  },
  cocktails: {
    index: '/cocktails/',
    drinkFull: '/cocktails/recipes/pear-and-rosemary-bellini/',
    drinkTiki: '/cocktails/recipes/cobras-fang/',
    rum: '/cocktails/reference/rum-categories/',
    glasses: '/cocktails/reference/glasses/',
  },
  // The site's 404 by its own path: the local server's own error page for a
  // missing URL is not the site's, and lays out at 980px.
  neither: { about: '/about/', notFound: '/404.html' },
};

const rows = [];
let browser;

async function settle(page) {
  try { await page.waitForLoadState('networkidle', { timeout: 15000 }); } catch (e) { /* carry on */ }
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.waitForTimeout(300);
}

async function fresh(vp) {
  const ctx = await browser.newContext(Object.assign({ reducedMotion: 'reduce' }, VIEWPORTS[vp]));
  const page = await ctx.newPage();
  return { ctx, page };
}

async function overflow(page, vp) {
  const w = VIEWPORTS[vp].viewport.width;
  const doc = await page.evaluate(() => document.documentElement.scrollWidth);
  return doc > w ? `OVERFLOW: page ${doc}px wide at ${w}` : '';
}

/** One shot. `how`: 'full' (whole page), 'screen' (viewport), or a CSS
 *  selector, cropped with padding from the whole page. */
async function shot(page, vp, file, how, url, action, shows) {
  const name = `${file}-${vp}.png`;
  try {
    await settle(page);
    const out = path.join(OUT, name);
    if (how === 'full') {
      await page.screenshot({ path: out, fullPage: true });
    } else if (how === 'screen') {
      await page.screenshot({ path: out });
    } else {
      const boxes = await page.evaluate((sels) => sels.map((s) => {
        const e = document.querySelector(s);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height };
      }).filter((b) => b && b.w > 0 && b.h > 0), [].concat(how));
      if (!boxes.length) throw new Error(`nothing to crop for ${how}`);
      const pad = 24;
      const x0 = Math.max(0, Math.min(...boxes.map((b) => b.x)) - pad);
      const y0 = Math.max(0, Math.min(...boxes.map((b) => b.y)) - pad);
      const x1 = Math.max(...boxes.map((b) => b.x + b.w)) + pad;
      const y1 = Math.max(...boxes.map((b) => b.y + b.h)) + pad;
      const docW = await page.evaluate(() => document.documentElement.scrollWidth);
      await page.screenshot({ path: out, fullPage: true, clip: { x: x0, y: y0, width: Math.min(x1, docW) - x0, height: y1 - y0 } });
    }
    const flag = await overflow(page, vp);
    rows.push({ name, url, vp, action, shows: shows + (flag ? ` — ${flag}` : ''), ok: true });
  } catch (e) {
    rows.push({ name, url, vp, action, shows: `FAILED: ${e.message.split('\n')[0]}`, ok: false });
  }
}

/** Run one scenario in its own context, so remembered index state cannot leak. */
async function scenario(vp, fn) {
  const { ctx, page } = await fresh(vp);
  try { await fn(page); } catch (e) {
    rows.push({ name: '(scenario)', url: page.url(), vp, action: 'scenario', shows: `FAILED: ${e.message.split('\n')[0]}`, ok: false });
  }
  await ctx.close();
}

async function go(page, url) {
  await page.goto(BASE + url, { waitUntil: 'load' });
  await settle(page);
}

async function tabTo(page, selector) {
  await page.mouse.click(1, 1);
  for (let i = 0; i < 120; i++) {
    await page.keyboard.press('Tab');
    const hit = await page.evaluate((s) => !!(document.activeElement && document.activeElement.matches(s)), selector);
    if (hit) return true;
  }
  throw new Error(`Tab never reached ${selector}`);
}

const slug = (s) => s.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase();

async function staticPages(vp) {
  const all = [
    ['food', 'index', PAGES.food.index, 'index'],
    ['food', 'recipe-full', PAGES.food.recipeFull, 'a recipe with notes and related recipes'],
    ['food', 'recipe-2', PAGES.food.recipe2, 'a second recipe'],
    ['food', 'ref-temperatures', PAGES.food.temps, 'internal temperatures reference'],
    ['food', 'ref-methods', PAGES.food.methods, 'cooking methods and timings reference'],
    ['cocktails', 'index', PAGES.cocktails.index, 'index'],
    ['cocktails', 'drink-full', PAGES.cocktails.drinkFull, 'a drink with suggestions, notes and a batch syrup'],
    ['cocktails', 'drink-tiki', PAGES.cocktails.drinkTiki, 'a tiki drink with a long chip row'],
    ['cocktails', 'ref-rum', PAGES.cocktails.rum, 'rum categories reference'],
    ['cocktails', 'ref-glasses', PAGES.cocktails.glasses, 'glasses reference'],
    ['neither', 'about', PAGES.neither.about, 'the about page'],
    ['neither', '404', PAGES.neither.notFound, 'the 404'],
  ];
  for (const [site, pg, url, what] of all) {
    await scenario(vp, async (page) => {
      await go(page, url);
      await shot(page, vp, `${site}-${pg}-rest-full`, 'full', url, 'load', `${what}, whole page`);
      await shot(page, vp, `${site}-${pg}-rest-screen`, 'screen', url, 'load', `${what}, first screen`);
    });
  }
}

async function chrome(vp) {
  if (vp !== 'desktop') return;
  const url = PAGES.food.recipeFull;
  const hovers = [
    ['.site-nav-icon-link:not(.site-about-link)', 'door', 'the door to the other site', '.site-header'],
    ['.site-about-link', 'about-mark', 'the ?? about link', '.site-header'],
    ['.back-to-index', 'back-arrow', 'the back arrow', '.page-furniture'],
    ['.btn-pdf', 'pdf', 'pdf above the head rule', '.recipe-head-end'],
    ['.site-footer a', 'footer-link', 'a footer column head', '.site-footer'],
  ];
  for (const [sel, key, what, crop] of hovers) {
    await scenario(vp, async (page) => {
      await go(page, url);
      await page.hover(sel);
      await shot(page, vp, `food-chrome-hover-${key}`, crop, url, `hover ${sel}`, `hover on ${what}`);
    });
  }
  await scenario(vp, async (page) => {
    await go(page, PAGES.cocktails.drinkTiki);
    await page.hover('.site-nav-icon-link:not(.site-about-link)');
    await shot(page, vp, 'cocktails-chrome-hover-door', '.site-header', PAGES.cocktails.drinkTiki, 'hover the door', 'hover on the door, cocktails');
  });
}

async function searchBox(vp) {
  for (const [site, url, q] of [['food', PAGES.food.recipeFull, 'ch'], ['cocktails', PAGES.cocktails.drinkTiki, 'gi']]) {
    await scenario(vp, async (page) => {
      await go(page, url);
      await page.click('.page-search-input');
      await shot(page, vp, `${site}-search-focused`, 'main > .page-search', url, 'click the box', 'search box focused, placeholder gone');
      await page.type('.page-search-input', q);
      await page.waitForSelector('.page-search-results:not([hidden])');
      await shot(page, vp, `${site}-search-dropdown`, ['main > .page-search', '.page-search-results'], url, `type "${q}"`, 'the dropdown, every group');
      const more = await page.$('button.page-search-more');
      if (more) {
        await more.click();
        await shot(page, vp, `${site}-search-more-open`, ['main > .page-search', '.page-search-results'], url, 'press a word group\'s +N more', 'a word group opened in place');
      }
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('ArrowDown');
      await shot(page, vp, `${site}-search-keyboard-row`, ['main > .page-search', '.page-search-results'], url, 'ArrowDown twice', 'the keyboard\'s highlighted row');
      if (vp === 'desktop') {
        await page.hover('.page-search-option >> nth=3');
        await shot(page, vp, `${site}-search-hover-option`, ['main > .page-search', '.page-search-results'], url, 'hover an option', 'hover on a result');
      }
    });
  }
}

const INDEX = {
  food: {
    url: PAGES.food.index,
    sections: [['star', '.btn-star'], ['mood', '.category--mood .btn-tag'], ['practicalities', '.category--practicalities .btn-tag']],
    include: ['#ingredient-search-box', '#ingredient-results-pool button', 'pot'],
    exclude: ['#exclude-search-box', '#exclude-results-pool button', 'pea'],
    name: ['#name-search-box', 'chicken'],
    next: '#recipe-page-next', seeAll: '#recipe-page-see-all',
    title: '.recipe-title-link', item: '.recipe-list > li',
  },
  cocktails: {
    url: PAGES.cocktails.index,
    sections: [['yolo', '.btn-chaos'], ['mood', '.drink-filter--mood .btn-mood'], ['hassle', '.drink-filter--hassle .btn-mood']],
    include: ['#drink-include', '#drink-include-pool button', 'gin'],
    exclude: ['#drink-exclude', '#drink-exclude-pool button', 'lime'],
    name: ['#drink-name', 'sour'],
    next: '#drink-page-next', seeAll: '#drink-page-see-all',
    title: '.drink-card-name a', item: '.drink-card',
  },
};

async function indexStates(vp) {
  for (const site of ['food', 'cocktails']) {
    const I = INDEX[site];
    for (const [sec, sel] of I.sections) {
      await scenario(vp, async (page) => {
        await go(page, I.url);
        await page.click(`${sel} >> nth=1`);
        await shot(page, vp, `${site}-index-chosen-${sec}`, '[data-filter-panel]', I.url, `choose a ${sec} chip`, `one ${sec} chip chosen`);
        if (vp === 'desktop' && sec === I.sections[0][0]) {
          await page.hover(`${sel} >> nth=1`);
          await shot(page, vp, `${site}-index-hover-chosen-chip`, `${sel}`, I.url, 'hover the chosen chip', 'hover on a chosen chip');
          await page.hover(`${sel} >> nth=2`);
          await shot(page, vp, `${site}-index-hover-resting-chip`, `${sel}`, I.url, 'hover a resting chip', 'hover on a resting chip');
        }
      });
    }
    if (vp === 'desktop') {
      await scenario(vp, async (page) => {
        await go(page, I.url);
        await tabTo(page, I.sections[0][1]);
        await shot(page, vp, `${site}-index-focus-chip`, '[data-filter-panel]', I.url, 'Tab to the first chip', 'keyboard focus on a chip');
      });
    }
    for (const [kind, [box, pool, q]] of [['include', I.include], ['exclude', I.exclude]]) {
      await scenario(vp, async (page) => {
        await go(page, I.url);
        await page.click(box);
        await page.type(box, q);
        await page.waitForTimeout(400);
        await shot(page, vp, `${site}-index-${kind}-typed`, '[data-filter-panel]', I.url, `type "${q}"`, `${kind === 'include' ? 'HAS TO HAVE' : 'LEAVE OUT'} typed, its pool showing`);
        await page.click(`${pool} >> nth=0`);
        await shot(page, vp, `${site}-index-${kind}-chosen`, '[data-filter-panel]', I.url, 'choose the first candidate', `${kind === 'include' ? 'HAS TO HAVE' : 'LEAVE OUT'} with an ingredient chosen`);
      });
    }
    await scenario(vp, async (page) => {
      await go(page, I.url);
      await page.click(I.name[0]);
      await page.type(I.name[0], I.name[1]);
      await page.waitForTimeout(400);
      await shot(page, vp, `${site}-index-name-typed`, 'full', I.url, `type "${I.name[1]}" in I KNOW WHAT I WANT`, 'name search with the title highlight in the list');
    });
    await scenario(vp, async (page) => {
      await go(page, I.url + '?q=qqqzzz');
      await shot(page, vp, `${site}-index-blank-canvas`, 'full', I.url + '?q=qqqzzz', 'a name that matches nothing', 'the empty state, "Blank canvas."');
    });
    await scenario(vp, async (page) => {
      await go(page, I.url);
      await page.click(I.next);
      await shot(page, vp, `${site}-index-page-2`, 'screen', I.url, 'press next', 'page 2 of the list');
      await page.click(I.seeAll);
      await shot(page, vp, `${site}-index-see-all`, 'full', I.url, 'press (see all)', 'the whole list');
    });
    if (vp === 'desktop') {
      await scenario(vp, async (page) => {
        await go(page, I.url);
        await page.hover(`${I.item} >> nth=0`);
        await shot(page, vp, `${site}-index-hover-item`, `${I.item}`, I.url, 'hover the first item', 'hover on a list item');
        await page.hover(`${I.title} >> nth=1`);
        await shot(page, vp, `${site}-index-hover-title`, `${I.item}:nth-child(2)`, I.url, 'hover a title', 'hover on an item title');
      });
    }
  }
}

async function pill(vp) {
  for (const [site, q] of [['food', '?star=beef'], ['cocktails', '?mood=tiki']]) {
    const url = INDEX[site].url;
    await scenario(vp, async (page) => {
      await go(page, url);
      await shot(page, vp, `${site}-pill-no-filter`, 'screen', url, 'load with no filter', 'the pill with nothing chosen');
      await go(page, url + q);
      await shot(page, vp, `${site}-pill-filtered`, 'screen', url + q, `load with ${q}`, 'the pill with a filter on');
      const down = await page.$('[data-results-pill-down]:not([hidden])');
      if (down) {
        await down.click();
        await page.waitForTimeout(800);
        await shot(page, vp, `${site}-pill-top`, 'screen', url + q, 'press N survivors ↓', '"top ↑ ×" on the results');
        await page.click('[data-results-pill-up]');
        await page.waitForTimeout(800);
        await shot(page, vp, `${site}-pill-back-at-filters`, 'screen', url + q, 'press top', 'back at STAR / YOLO? after top');
      }
    });
  }
}

async function cocktailsExtras(vp) {
  const url = PAGES.cocktails.index;
  // The tagline is a reveal: the "?" where there is no hover, the card's own
  // hover where there is (#1292), so desktop hovers and the others press.
  await scenario(vp, async (page) => {
    await go(page, url);
    if (vp === 'desktop') {
      await page.hover('.drink-card >> nth=0');
      await shot(page, vp, 'cocktails-index-card-tagline', '.drink-card', url, 'hover a card', 'a card with its tagline revealed by hover');
    } else {
      await page.click('.btn-card-tagline >> nth=0');
      await shot(page, vp, 'cocktails-index-card-tagline', '.drink-card:has(.btn-card-tagline[aria-pressed="true"])', url, 'press a card\'s ?', 'a card with its tagline open');
    }
  });
  await scenario(vp, async (page) => {
    await go(page, url);
    await page.click('.btn-universe-again');
    await page.waitForTimeout(400);
    await shot(page, vp, 'cocktails-index-deal-again', '.universe', url, 'press deal again', 'the universe line after a new deal');
  });
  for (const [where, u] of [['index', url], ['drink', PAGES.cocktails.drinkTiki]]) {
    await scenario(vp, async (page) => {
      await go(page, u);
      await page.click('.ship-key-open >> nth=0');
      await page.waitForTimeout(300);
      await shot(page, vp, `cocktails-${where}-ship-key-dialog`, 'screen', u, 'open the ship key', 'the ship key dialog');
    });
  }
  await scenario(vp, async (page) => {
    await go(page, url);
    await page.click('.drink-card-ship >> nth=0');
    await page.waitForTimeout(400);
    await shot(page, vp, 'cocktails-index-ship-filter', 'full', url, 'press a card\'s ship mark', 'the SHIP IT? filter on, with "× clear ship"');
  });
}

async function shortlist(vp) {
  for (const [site, pages, index, actionsCrop] of [
    ['food', [PAGES.food.recipeFull, PAGES.food.recipe2], PAGES.food.index, '.recipe-section-heading-row'],
    ['cocktails', [PAGES.cocktails.drinkFull, PAGES.cocktails.drinkTiki], PAGES.cocktails.index, '.cocktail-controls'],
  ]) {
    await scenario(vp, async (page) => {
      for (const [i, p] of pages.entries()) {
        await go(page, p);
        await page.click('.page-actions .btn-shortlist');
        await page.waitForTimeout(300);
        if (i === 0) await shot(page, vp, `${site}-page-shortlisted`, actionsCrop, p, 'press + SHORTLIST', 'the page shortlisted, with SEE SHORTLIST (N)');
      }
      await go(page, index);
      await page.click(`${INDEX[site].title} >> nth=0`).catch(() => {});
      await settle(page);
      await page.click('.page-actions .btn-shortlist').catch(() => {});
      await go(page, index + '?shortlist=1');
      await shot(page, vp, `${site}-index-shortlist-view`, 'full', index + '?shortlist=1', 'shortlist three pages, open ?shortlist=1', `the shortlist view${site === 'food' ? ', with the shopping list' : ''}`);
      const slugs = pages.map((p) => p.split('/').filter(Boolean).pop()).join(',');
      await go(page, index + '?shortlist=' + slugs);
      await shot(page, vp, `${site}-index-shared-shortlist`, 'full', index + '?shortlist=' + slugs, 'open a shared shortlist link', 'a shortlist someone sent');
    });
  }
}

async function recipeStates(vp) {
  await scenario(vp, async (page) => {
    const u = PAGES.food.recipeFull;
    await go(page, u);
    await page.click('.recipe-scale-plus >> nth=0');
    await page.click('.recipe-scale-plus >> nth=0');
    await shot(page, vp, 'food-recipe-scaled-up', 'full', u, 'press + twice on the scaler', 'the recipe scaled up');
    await page.click('.recipe-scale-minus >> nth=0');
    await page.click('.recipe-scale-minus >> nth=0');
    await page.click('.recipe-scale-minus >> nth=0');
    await shot(page, vp, 'food-recipe-scaled-down', '.recipe-section-ingredients', u, 'press − three times', 'the recipe scaled down');
  });
  await scenario(vp, async (page) => {
    const u = PAGES.cocktails.drinkFull;
    await go(page, u);
    await page.click('#cocktail-make');
    await page.waitForTimeout(300);
    await shot(page, vp, 'cocktails-drink-make-it', 'full', u, 'switch to MAKE IT', 'the drink in make-it mode');
    await page.click('.cocktail-scale-plus');
    await page.click('.cocktail-scale-plus');
    await shot(page, vp, 'cocktails-drink-scaled', 'full', u, 'press + twice on the drinks scaler', 'the drink scaled to three');
  });
  await scenario(vp, async (page) => {
    const u = PAGES.food.methods;
    await go(page, u);
    await page.selectOption('#ct-protein', { index: 2 });
    await page.fill('#ct-weight', '4');
    await page.keyboard.press('Tab');
    await page.waitForTimeout(400);
    await shot(page, vp, 'food-ref-methods-changed', 'full', u, 'choose the third cut, weight 4', 'the methods page for another cut and weight');
  });
}

async function print() {
  for (const [site, u] of [['food', PAGES.food.recipeFull], ['cocktails', PAGES.cocktails.drinkFull]]) {
    await scenario('desktop', async (page) => {
      await page.emulateMedia({ media: 'print' });
      await go(page, u);
      await shot(page, 'desktop', `${site}-print`, 'full', u, 'emulate print media', 'the page as printed');
    });
  }
}

// Every stateful control found by grepping the templates and _sass for
// :hover, :focus-visible, aria-pressed, aria-expanded, <dialog and [hidden],
// and whether this set captures it.
const CONTROLS = `
## Stateful controls found, and what was captured

| control | where | captured |
|---|---|---|
| door to the other site, \`??\` | header, both sites | hover (desktop) |
| back arrow, print · pdf | recipe and drink pages | hover (desktop); print is the PDF link only in the deployed build, as pdf |
| footer column heads | every page | hover (desktop) |
| search box: focus, dropdown, "+N more" (link and in-place), keyboard row, option hover | every site page | all |
| filter chips: rest, chosen, hover, keyboard focus | both indexes, every section | all (hover and focus on desktop) |
| HAS TO HAVE / LEAVE OUT: typed pool, chosen chip with × | both indexes | both |
| I KNOW WHAT I WANT, title highlight | both indexes | yes |
| per-section "× clear", typing boxes' "× clear" | both indexes | shown in the chosen-state shots; no hover shot of their own |
| results pill: survivors ↓, top ↑ ×, survivors × | both indexes | all faces (top ↑ only where the list is below the filters: phone, iPad) |
| pagination next / (see all) | both indexes | both |
| list item and title hover | both indexes | yes (desktop) |
| card tagline "?" (aria-pressed) | cocktails cards | pressed (phone, iPad); revealed by hover on desktop, where the "?" is hidden by design (#1292) |
| deal again | cocktails index | yes |
| ship key dialog (\`<dialog>\`) | cocktails index and drink pages | yes |
| SHIP IT? filter and "× clear ship" | cocktails index | yes |
| + SHORTLIST (aria-pressed), SEE SHORTLIST (N) | recipe and drink pages, index cards | page button on; card buttons appear on the shortlist view |
| shortlist view, shopping list, shared link | both indexes | all |
| scaler (+ / −) | recipe and drink pages | yes |
| READ IT / MAKE IT | drink pages | MAKE IT on |
| cut and weight | methods reference page | another cut and weight |
| print media | recipe and drink | yes (desktop) |
| hide / show drafts | both indexes | skipped: local builds only, never deployed |
| short-method toggle | food recipes | skipped: switched off in _config.yml |
| magic bag pages | food | skipped: no published entries |
| root page | site root | skipped: a redirect to food |
| hover at phone and iPad widths | everywhere | skipped: not a state a touch screen reaches |
`;

function manifest() {
  const lines = [];
  lines.push('# Design review screenshot set', '');
  lines.push(`Captured from commit \`${commit}\` on ${new Date().toISOString().slice(0, 10)}, from scripts/browser/build.sh's build (what deploys), served locally.`, '');
  lines.push('Widths: phone 390×844 at 2×, iPad portrait 1024×1366 at 2×, desktop 1280×900 at 1×. Hover and keyboard focus are desktop only. Reduced motion is on, so nothing is mid-animation. Both indexes shuffle and cocktails deals a random drink, so lists differ from shot to shot.', '');
  const ok = rows.filter((r) => r.ok).length;
  lines.push(`${ok} images, ${rows.length - ok} failed.`, '');
  lines.push('| file | width | URL | action | shows |', '|---|---|---|---|---|');
  for (const r of rows) lines.push(`| ${r.ok ? `[${r.name}](${r.name})` : r.name} | ${r.vp} | ${r.url.replace(/^https?:\/\/[^/]+/, '')} | ${r.action} | ${r.shows} |`);
  return lines.join('\n') + '\n' + CONTROLS;
}

(async () => {
  browser = await chromium.launch();
  for (const vp of Object.keys(VIEWPORTS)) {
    await staticPages(vp);
    await chrome(vp);
    await searchBox(vp);
    await indexStates(vp);
    await pill(vp);
    await cocktailsExtras(vp);
    await shortlist(vp);
    await recipeStates(vp);
  }
  await print();
  await browser.close();
  fs.writeFileSync(path.join(OUT, 'shots.json'), JSON.stringify(rows, null, 1));
  fs.writeFileSync(path.join(OUT, 'index.md'), manifest());
  console.log(`${rows.filter((r) => r.ok).length} ok, ${rows.filter((r) => !r.ok).length} failed`);
  rows.filter((r) => !r.ok).forEach((r) => console.log('FAILED', r.vp, r.name, r.shows));
  rows.filter((r) => /OVERFLOW/.test(r.shows)).forEach((r) => console.log('OVERFLOW', r.vp, r.name));
})();
