#!/usr/bin/env node
/*
 * Screenshot every rendered HTML preview into a PNG using puppeteer.
 *
 * Reads from emails/preview/out/ and emails/preview/out_before/, writes the
 * resulting PNGs side-by-side in emails/preview/screenshots/.
 */

const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");

const PREVIEW_DIR = path.resolve(__dirname);
const OUT_DIRS = ["out_before", "out"];
const SHOTS_DIR = path.join(PREVIEW_DIR, "screenshots");

async function main() {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();
  // 700-wide window so the 600px email body has room to breathe.
  await page.setViewport({ width: 700, height: 900, deviceScaleFactor: 1 });

  for (const dir of OUT_DIRS) {
    const inDir = path.join(PREVIEW_DIR, dir);
    const outDir = path.join(SHOTS_DIR, dir);
    fs.mkdirSync(outDir, { recursive: true });

    const files = fs.readdirSync(inDir).filter((f) => f.endsWith(".html"));
    for (const file of files) {
      const url = "file://" + path.join(inDir, file);
      await page.goto(url, { waitUntil: "networkidle0", timeout: 15000 });
      const target = path.join(outDir, file.replace(/\.html$/, ".png"));
      await page.screenshot({ path: target, fullPage: true });
      console.log(`shot ${dir}/${file} -> ${path.relative(PREVIEW_DIR, target)}`);
    }
  }

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
