// Cut a tall PNG into pieces short enough to read, top to bottom.
//
// USAGE:
//   node tools/dev/slice-png.js <in.png> [<slice-height>]
//
// Writes <in>-1.png, <in>-2.png, ... beside the input, each <slice-height>
// pixels tall (default 1600) apart from the last. The input must be under
// tmp/. Chromium does the cutting, so no image library is needed: the PNG is
// shown at 1:1 and each slice is a clipped screenshot of it.
//
// Needs WITH_PLAYWRIGHT=1 in kit.env (see tools/dev/shoot.js).
const fs = require('fs');
const path = require('path');

const [input, heightArg] = process.argv.slice(2);
const sliceHeight = Number(heightArg || 1600);
if (!input || !/^tmp\/[A-Za-z0-9._/-]+\.png$/.test(input) || input.includes('..')) {
  console.error('slice-png.js: give a .png under tmp/\nusage: node tools/dev/slice-png.js <in.png> [<slice-height>]');
  process.exit(2);
}
if (!Number.isInteger(sliceHeight) || sliceHeight < 100) {
  console.error(`slice-png.js: slice height must be a whole number of at least 100, not '${heightArg}'`);
  process.exit(2);
}

(async () => {
  // Required after the arguments are checked, so a usage error needs no browser.
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  // A plain page holding the image at its own size in the top left corner,
  // so a clip of the page is a slice of it. The image goes in as a data
  // URL: a blank page may not load a file:// image, and Chromium's own
  // image viewer centres and shrinks a tall one and keeps its page the
  // viewport's height, so a clip below the fold is "outside the image".
  const data = 'data:image/png;base64,' + fs.readFileSync(path.resolve(input)).toString('base64');
  await page.setContent(`<body style="margin:0"><img src="${data}" style="display:block"></body>`, { waitUntil: 'load' });
  const { width, height } = await page.evaluate(() => {
    const img = document.querySelector('img');
    return { width: img.naturalWidth, height: img.naturalHeight };
  });
  await page.setViewportSize({ width, height: Math.min(height, sliceHeight) });
  const stem = input.replace(/\.png$/, '');
  let n = 0;
  for (let y = 0; y < height; y += sliceHeight) {
    n += 1;
    const out = `${stem}-${n}.png`;
    await page.screenshot({ path: out, fullPage: true, clip: { x: 0, y, width, height: Math.min(sliceHeight, height - y) } });
    console.log(`${out} y=${y}`);
  }
  await browser.close();
})();
