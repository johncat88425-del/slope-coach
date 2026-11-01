import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import puppeteer from '/Users/aacc/Documents/slope-coach/frontend/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT_DIR = '/Users/aacc/Documents/slope-coach/data/e2e/T216';
const BASE_URL = 'http://127.0.0.1:4173';
const DEMO_OWN_2 = '/Users/aacc/Documents/slope-coach/data/demo/real_own_2.json';
const MAX_IMAGE_BYTES = 300 * 1024; // 300 KB limit per task requirements

const VIEWPORTS = [
  { name: '1440px', width: 1440, height: 900, isMobile: false, hasTouch: false },
  { name: '390px', width: 390, height: 844, isMobile: true, hasTouch: true }
];

const PAGES = [
  { route: 'home', hash: '#home', label: 'Home Page' },
  { route: 'results', hash: '#wall', label: 'Results Wall (with Cars card)' },
  { route: 'how', hash: '#how', label: 'How It Works Page' },
  { route: 'audit', hash: '#audit', label: 'Audit / Upload Page' }
];

async function verifyAndLog(filePath, label) {
  const stats = fs.statSync(filePath);
  const buffer = fs.readFileSync(filePath);
  const hash = crypto.createHash('md5').update(buffer).digest('hex');
  const sizeKB = (stats.size / 1024).toFixed(1);
  console.log(`[Screenshot] ${label}: ${path.basename(filePath)} (${sizeKB} KB, md5: ${hash})`);
  if (stats.size > MAX_IMAGE_BYTES) {
    throw new Error(`Screenshot ${filePath} exceeds 300 KB: ${stats.size} bytes`);
  }
  return { path: filePath, sizeKB, hash };
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  console.log('====================================================');
  console.log('=== T216 Regression Screenshots (1440px & 390px) ===');
  console.log('====================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const captured = [];

  try {
    for (const vp of VIEWPORTS) {
      console.log(`\n--- Capturing for Viewport: ${vp.name} (${vp.width}x${vp.height}) ---`);
      const page = await browser.newPage();
      await page.setViewport({
        width: vp.width,
        height: vp.height,
        deviceScaleFactor: 1,
        isMobile: vp.isMobile,
        hasTouch: vp.hasTouch
      });

      // 1. Home
      await page.goto(`${BASE_URL}/#home`, { waitUntil: 'networkidle0' });
      await page.waitForSelector('.home-page', { timeout: 5000 });
      // Allow animation to settle
      await new Promise(r => setTimeout(r, 2500));
      const homeFile = path.join(OUT_DIR, `page1_home_${vp.name}.png`);
      await page.screenshot({ path: homeFile, fullPage: false });
      captured.push(await verifyAndLog(homeFile, `Home (${vp.name})`));

      // 2. Results Wall
      await page.goto(`${BASE_URL}/#wall`, { waitUntil: 'networkidle0' });
      await page.waitForSelector('[data-testid="reviewer-opening"]', { timeout: 5000 });
      // Verify Cars card exists (from T218)
      const carsCard = await page.$('.car-preview, [data-record-key="cars"]');
      if (carsCard) {
        console.log(`[T218 Verify] Found Cars preview card on Results page (${vp.name})`);
      }
      await new Promise(r => setTimeout(r, 1000));
      const resultsFile = path.join(OUT_DIR, `page2_results_${vp.name}.png`);
      await page.screenshot({ path: resultsFile, fullPage: false });
      captured.push(await verifyAndLog(resultsFile, `Results Wall (${vp.name})`));

      // 3. How it works
      await page.goto(`${BASE_URL}/#how`, { waitUntil: 'networkidle0' });
      await page.waitForSelector('.process-steps', { timeout: 5000 });
      await new Promise(r => setTimeout(r, 1000));
      const howFile = path.join(OUT_DIR, `page3_how_${vp.name}.png`);
      await page.screenshot({ path: howFile, fullPage: false });
      captured.push(await verifyAndLog(howFile, `How It Works (${vp.name})`));

      // 4. Audit / Upload Page (with loaded demo result showing T210 and T218 UI additions)
      await page.goto(`${BASE_URL}/#audit`, { waitUntil: 'networkidle0' });
      await page.waitForSelector('[data-testid="interview-panel"]', { timeout: 5000 });
      
      // Load real_own_2 to show result card
      const offlineSummary = await page.$('[data-testid="offline-import"] summary');
      if (offlineSummary) {
        await offlineSummary.click();
        await new Promise(r => setTimeout(r, 400));
      }
      const importInput = await page.$('[data-testid="audit-import-json"]');
      await importInput.uploadFile(DEMO_OWN_2);
      await page.waitForSelector('[data-testid="audit-result"]', { timeout: 5000 });
      
      // Verify T218 download button outside details
      const visibleDownloadBtn = await page.$('.result-download, button[data-testid="result-download"]');
      if (visibleDownloadBtn) {
        console.log(`[T218 Verify] Found visible uncollapsed share card download button (${vp.name})`);
      }
      await new Promise(r => setTimeout(r, 1000));
      const auditFile = path.join(OUT_DIR, `page4_audit_${vp.name}.png`);
      await page.screenshot({ path: auditFile, fullPage: false });
      captured.push(await verifyAndLog(auditFile, `Audit Page (${vp.name})`));

      await page.close();
    }

    console.log('\n====================================================');
    console.log('=== SCREENSHOT HASH SUMMARY ===');
    console.log('====================================================');
    const hashes = new Set(captured.map(c => c.hash));
    console.log(`Total captured: ${captured.length}, Unique MD5 hashes: ${hashes.size}`);
    if (hashes.size !== captured.length) {
      throw new Error('Duplicate screenshot hash detected!');
    }
    console.log('All 8 screenshots verified distinct and under 300 KB limit!');

  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error('Regression capture failed:', err);
  process.exit(1);
});
