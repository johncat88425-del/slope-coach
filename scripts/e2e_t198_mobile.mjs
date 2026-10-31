import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import puppeteer from '../frontend/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT_DIR = './data/e2e/T198';
const BASE_URL = 'http://127.0.0.1:5173';
const DEMO_OWN_2 = './data/demo/real_own_2.json';
const DEMO_CLIP_4 = './data/demo/generated_meta_clip4.json';
const MAX_IMAGE_BYTES = 300 * 1024; // 300 KB limit per task requirements

const DEVICES = [
  {
    name: 'iphone14',
    title: 'iPhone 14',
    viewport: { width: 390, height: 844, deviceScaleFactor: 1, isMobile: true, hasTouch: true },
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
  },
  {
    name: 'pixel7',
    title: 'Pixel 7',
    viewport: { width: 412, height: 915, deviceScaleFactor: 1, isMobile: true, hasTouch: true },
    userAgent: 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
  }
];

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  console.log('====================================================');
  console.log('=== T198 Mobile Emulation & End-to-End Walkthrough ===');
  console.log('====================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const capturedFiles = [];

  for (const dev of DEVICES) {
    console.log(`\n====================================================`);
    console.log(`>>> Testing on ${dev.title} (${dev.viewport.width}x${dev.viewport.height})`);
    console.log(`====================================================`);

    const page = await browser.newPage();
    await page.setViewport(dev.viewport);
    await page.setUserAgent(dev.userAgent);

    async function saveScreenshot(filename, fullPage = false) {
      const filePath = path.join(OUT_DIR, filename);
      await page.screenshot({ path: filePath, fullPage });
      const stats = fs.statSync(filePath);
      const hash = crypto.createHash('md5').update(fs.readFileSync(filePath)).digest('hex');
      console.log(`Saved ${filename} (${(stats.size / 1024).toFixed(1)} KB, MD5: ${hash})`);
      if (stats.size > MAX_IMAGE_BYTES) {
        throw new Error(`File ${filename} exceeds 300 KB limit! Size: ${stats.size} bytes`);
      }
      capturedFiles.push({ filename, filePath, size: stats.size, hash, device: dev.title });
    }

    // Step 1: Upload View on #audit
    console.log(`\n[${dev.title}] 1. Navigating to #audit (upload view)...`);
    await page.goto(`${BASE_URL}/#audit`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('.audit-flow');
    await new Promise(r => setTimeout(r, 500));

    // Verify layout and overflow
    const uploadMetrics = await page.evaluate(() => {
      const scrollWidth = document.documentElement.scrollWidth;
      const clientWidth = document.documentElement.clientWidth;
      return { scrollWidth, clientWidth, hasOverflow: scrollWidth > clientWidth };
    });
    console.log(`[${dev.title}] Upload screen metrics:`, uploadMetrics);
    if (uploadMetrics.hasOverflow) {
      throw new Error(`Horizontal overflow on ${dev.title} upload screen! scrollWidth: ${uploadMetrics.scrollWidth}, clientWidth: ${uploadMetrics.clientWidth}`);
    }
    await saveScreenshot(`${dev.name}_01_upload_screen.png`);

    // Step 2: Upload / Replay demo case (real_own_2.json)
    console.log(`\n[${dev.title}] 2. Uploading demo case (${path.basename(DEMO_OWN_2)})...`);
    await page.evaluate(() => {
      const details = document.querySelector('[data-testid="offline-import"]');
      if (details) details.open = true;
    });
    await new Promise(r => setTimeout(r, 200));

    const importInput = await page.$('[data-testid="audit-import-json"]');
    if (!importInput) throw new Error('Offline import input not found!');
    await importInput.uploadFile(DEMO_OWN_2);

    await page.waitForSelector('[data-testid="audit-result"]');
    await new Promise(r => setTimeout(r, 600));

    const resultMetrics = await page.evaluate(() => {
      const scrollWidth = document.documentElement.scrollWidth;
      const clientWidth = document.documentElement.clientWidth;
      const verdict = document.querySelector('[data-testid="audit-verdict"]')?.textContent?.trim();
      const buttons = Array.from(document.querySelectorAll('button:not([hidden]), a.next, a.primary')).filter(b => {
        const r = b.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      }).map(b => ({
        text: b.textContent?.trim().slice(0, 24),
        height: Math.round(b.getBoundingClientRect().height)
      }));
      return {
        verdict,
        scrollWidth,
        clientWidth,
        hasOverflow: scrollWidth > clientWidth,
        touchButtons: buttons
      };
    });
    console.log(`[${dev.title}] Result screen metrics: verdict="${resultMetrics.verdict}", overflow=${resultMetrics.hasOverflow}`);
    console.log(`[${dev.title}] Active buttons touch target heights:`, resultMetrics.touchButtons);

    if (resultMetrics.hasOverflow) {
      throw new Error(`Horizontal overflow on ${dev.title} result screen!`);
    }
    const smallButtons = resultMetrics.touchButtons.filter(b => b.height < 44);
    if (smallButtons.length > 0) {
      console.warn(`[${dev.title}] Warning: Some visible buttons are < 44px:`, smallButtons);
    }
    await saveScreenshot(`${dev.name}_02_result_screen.png`);

    // Step 3: Expand Details section
    console.log(`\n[${dev.title}] 3. Expanding Details section...`);
    await page.evaluate(() => {
      const details = document.querySelector('[data-testid="audit-details"]');
      if (details) {
        details.open = true;
        details.scrollIntoView();
      }
    });
    await new Promise(r => setTimeout(r, 500));
    await saveScreenshot(`${dev.name}_03_result_details.png`);

    // Step 4: Results Wall tap-to-expand card check
    console.log(`\n[${dev.title}] 4. Results wall (#wall) tap-to-expand card check...`);
    await page.goto(`${BASE_URL}/#wall`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('[data-testid="results-wall"]');
    await new Promise(r => setTimeout(r, 500));

    const firstCard = await page.$('[data-testid="opening-card"]');
    if (!firstCard) throw new Error('Opening cards not found on #wall!');

    // Tap first card to expand
    console.log(`[${dev.title}] Tapping first opening card...`);
    await firstCard.tap();
    await new Promise(r => setTimeout(r, 500));

    const tapState = await page.evaluate(() => {
      const card = document.querySelector('[data-testid="opening-card"]');
      const ev = card.querySelector('.preview-evidence');
      return {
        cardOpenClass: card.classList.contains('is-open'),
        evMaxHeight: window.getComputedStyle(ev).maxHeight,
        evOpacity: window.getComputedStyle(ev).opacity
      };
    });
    console.log(`[${dev.title}] Card state after tap:`, tapState);
    if (tapState.evOpacity !== '1') {
      console.warn(`[${dev.title}] Warning: evidence opacity is not 1 after tap:`, tapState);
    }
    await saveScreenshot(`${dev.name}_04_wall_card_expanded.png`);

    // If Pixel 7, also test inconsistent case (generated_meta_clip4.json)
    if (dev.name === 'pixel7') {
      console.log(`\n[${dev.title}] 5. Testing inconsistent clip (${path.basename(DEMO_CLIP_4)})...`);
      await page.goto(`${BASE_URL}/#audit`, { waitUntil: 'networkidle0' });
      await page.waitForSelector('.audit-flow');
      await page.evaluate(() => {
        const details = document.querySelector('[data-testid="offline-import"]');
        if (details) details.open = true;
      });
      await new Promise(r => setTimeout(r, 200));

      const p7Input = await page.$('[data-testid="audit-import-json"]');
      await p7Input.uploadFile(DEMO_CLIP_4);
      await page.waitForSelector('[data-testid="audit-result"]');
      await new Promise(r => setTimeout(r, 600));

      const incVerdict = await page.$eval('[data-testid="audit-verdict"]', el => el.textContent.trim());
      console.log(`[${dev.title}] Inconsistent clip verdict:`, incVerdict);
      await saveScreenshot(`${dev.name}_05_inconsistent_result.png`);
    }

    await page.close();
  }

  await browser.close();

  // ==========================================
  // Summary & Size Verification
  // ==========================================
  console.log('\n====================================================');
  console.log('=== SUMMARY OF T198 MOBILE SCREENSHOTS ===');
  console.log('====================================================');
  let allUnderLimit = true;
  for (const item of capturedFiles) {
    const pass = item.size <= MAX_IMAGE_BYTES;
    if (!pass) allUnderLimit = false;
    console.log(`- [${item.device.padEnd(9)}] ${item.filename.padEnd(35)}: ${(item.size / 1024).toFixed(1).padStart(6)} KB  [${pass ? 'PASS' : 'FAIL >300KB'}]  MD5: ${item.hash}`);
  }

  if (!allUnderLimit) {
    throw new Error('Some screenshots exceeded the 300 KB limit!');
  }
  console.log('\nSUCCESS: All T198 mobile screenshots verified under 300 KB and captured successfully!\n');
}

main().catch(err => {
  console.error('\nT198 E2E SCRIPT FAILED:', err);
  process.exit(1);
});
