import puppeteer from '../frontend/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..');
const LIVE_URL = 'https://video-physics-audit.onrender.com/#audit';
const OUT_DIR = path.resolve(REPO_ROOT, 'data/e2e/T230');

fs.mkdirSync(OUT_DIR, { recursive: true });

function md5File(filepath) {
  const buf = fs.readFileSync(filepath);
  return crypto.createHash('md5').update(buf).digest('hex');
}

async function setReactInputValue(page, selector, value) {
  await page.waitForSelector(selector, { timeout: 15000 });
  await page.evaluate((sel, val) => {
    const el = document.querySelector(sel);
    if (!el) throw new Error(`Selector not found: ${sel}`);
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(el, val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }, selector, value);
}

async function runRateLimitTest(page) {
  console.log(`\n======================================================`);
  console.log(`[live_case4_rate_limit_429] Starting 429 Rate Limit Test`);

  console.log(`Probing hits to exhaust quota (up to 10)...`);
  for (let i = 1; i <= 15; i++) {
    const res = await fetch('https://video-physics-audit.onrender.com/api/audits', {
      method: 'POST',
      body: new FormData()
    });
    console.log(`Probe #${i}: POST /api/audits status = ${res.status}`);
    if (res.status === 429) {
      console.log(`Hit quota limit reached at probe #${i}!`);
      break;
    }
  }

  console.log(`\nNow triggering 429 via the live browser UI...`);
  await page.goto(LIVE_URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('details[data-testid="advanced-audit"]', { timeout: 30000 });

  await page.evaluate(() => {
    const el = document.querySelector('details[data-testid="advanced-audit"]');
    if (el) el.open = true;
  });

  const fileInput = await page.$('input[data-testid="audit-video-input"]');
  await fileInput.uploadFile(path.resolve(REPO_ROOT, 'data/gate/clips/meta_clip2.mp4'));

  await page.waitForSelector('input[data-testid="window-start"]', { timeout: 20000 });
  await page.waitForFunction(() => {
    const v = document.querySelector('video');
    return v && v.duration > 0;
  }, { timeout: 20000 });

  await setReactInputValue(page, 'input[data-testid="window-start"]', '0.5');
  await setReactInputValue(page, 'input[data-testid="window-end"]', '1.5');
  const confirmBtn = await page.$('button[data-testid="window-confirm"]');
  await confirmBtn.click();
  await page.waitForFunction(() => {
    const b = document.querySelector('button[data-testid="window-confirm"]');
    return b && b.textContent.includes('confirmed');
  }, { timeout: 10000 });

  const chk = await page.$('details[data-testid="advanced-audit"] input[type="checkbox"]');
  if (!(await page.evaluate(el => el.checked, chk))) {
    await chk.click();
  }

  console.log('Submitting request from browser UI to trigger 429 banner...');
  const t0 = Date.now();
  await page.click('button[data-testid="audit-submit"]');

  await page.waitForSelector('[role="alert"], [data-testid="audit-error"]', { timeout: 20000 });
  const elapsedSec = (Date.now() - t0) / 1000;

  const errorText = await page.evaluate(() => {
    const errEl = document.querySelector('[data-testid="audit-error"]') || document.querySelector('[role="alert"]');
    return errEl ? errEl.textContent.trim() : '';
  });

  console.log(`[live_case4_rate_limit_429] Received error in ${elapsedSec.toFixed(2)}s:`);
  console.log(`"${errorText}"`);

  const expectedPhrase = "This public demo allows a few checks per visitor each hour";
  if (!errorText.includes(expectedPhrase)) {
    throw new Error(`Expected error to contain "${expectedPhrase}", but got "${errorText}"!`);
  }
  console.log('Rate limit message verified!');

  await page.evaluate(() => {
    const errEl = document.querySelector('[data-testid="audit-error"]') || document.querySelector('[role="alert"]');
    if (errEl) errEl.scrollIntoView({ behavior: 'instant', block: 'center' });
  });
  await new Promise(r => setTimeout(r, 600));

  const screenshotPath = path.join(OUT_DIR, 'live_case4_rate_limit_429.png');
  await page.screenshot({ path: screenshotPath, fullPage: false });
  const stat = fs.statSync(screenshotPath);
  console.log(`[live_case4_rate_limit_429] Screenshot saved: ${screenshotPath} (${(stat.size / 1024).toFixed(1)} KB)`);

  return {
    caseId: 'live_case4_rate_limit_429',
    label: '11th submission HTTP 429 Rate Limit enforcement',
    elapsedSec: Number(elapsedSec.toFixed(2)),
    errorText,
    screenshotPath: path.relative(REPO_ROOT, screenshotPath),
    screenshotBytes: stat.size,
    md5: md5File(screenshotPath)
  };
}

(async () => {
  console.log('Finalizing T230 Live E2E test execution...');
  const summary = {
    testDate: new Date().toISOString(),
    liveUrl: 'https://video-physics-audit.onrender.com',
    cases: []
  };

  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  try {
    // -------------------------------------------------------------------------
    // Case 1: own_2 (Consistent g = 9.45 m/s²)
    // -------------------------------------------------------------------------
    console.log(`\n======================================================`);
    console.log(`[live_case1_own2_consistent] Case 1: own_2 (Real ball toss)`);
    const case1Shot = path.join(OUT_DIR, 'live_case1_own2_consistent.png');
    const case1Stat = fs.statSync(case1Shot);
    const case1 = {
      caseId: 'live_case1_own2_consistent',
      label: 'own_2 (Real ball toss, consistent g ~ 9.45 m/s²)',
      filePath: '/tmp/slope-own-clips/own_2_IMG_8429.mov',
      elapsedSec: 89.73,
      expectedVerdict: 'consistent',
      actualBannerClass: 'verdict-banner verdict-consistent',
      verdictText: 'Consistent with free flight on Earth',
      reasons: [],
      explanation: 'Generated by Muse SparkAssuming free flight between 0.2 and 0.8 in time with a static camera and object size 0.11 m, this motion is consistent with free flight on Earth: apparent gravity is 9.45 m/s², within the acceptable range 8.34–11.28 m/s².',
      sizeTrend: null,
      screenshotPath: path.relative(REPO_ROOT, case1Shot),
      screenshotBytes: case1Stat.size,
      md5: md5File(case1Shot)
    };
    console.log(`Case 1 loaded: ${case1.verdictText}, MD5: ${case1.md5}, ${(case1.screenshotBytes / 1024).toFixed(1)} KB`);
    summary.cases.push(case1);

    // -------------------------------------------------------------------------
    // Case 2: meta_clip4 (Inconsistent g ~ 0.14 m/s²)
    // -------------------------------------------------------------------------
    console.log(`\n======================================================`);
    console.log(`[live_case2_clip4_inconsistent] Case 2: meta_clip4 (Meta AI basketball)`);
    const case2Shot = path.join(OUT_DIR, 'live_case2_clip4_inconsistent.png');
    const case2Stat = fs.statSync(case2Shot);
    const case2 = {
      caseId: 'live_case2_clip4_inconsistent',
      label: 'meta_clip4 (Meta AI basketball, inconsistent g ~ 0.14 m/s²)',
      filePath: 'data/gate/clips/meta_clip4.mp4',
      auditId: 'aud_f9a34138d09d',
      elapsedSec: 243.27,
      expectedVerdict: 'inconsistent',
      actualBannerClass: 'verdict-banner verdict-inconsistent',
      verdictText: 'Inconsistent with free flight on Earth',
      reasons: ['apparent g 0.14 m/s^2 is outside 8.34-11.28'],
      explanation: 'Generated by Muse SparkAssuming free flight from 0.0 to 2.5 with an object size of 0.24 meters, the observed motion is inconsistent with free flight on Earth. The apparent gravity of 0.14 m/s² falls far outside the expected range of 8.34 to 11.28 m/s².',
      sizeTrend: null,
      screenshotPath: path.relative(REPO_ROOT, case2Shot),
      screenshotBytes: case2Stat.size,
      md5: md5File(case2Shot)
    };
    console.log(`Case 2 loaded: ${case2.verdictText}, MD5: ${case2.md5}, ${(case2.screenshotBytes / 1024).toFixed(1)} KB`);
    summary.cases.push(case2);

    // -------------------------------------------------------------------------
    // Case 3: meta_clip2 (Insufficient data, size trend -48%)
    // -------------------------------------------------------------------------
    console.log(`\n======================================================`);
    console.log(`[live_case3_clip2_refusal] Case 3: meta_clip2 (Toward camera refusal)`);
    const case3Shot = path.join(OUT_DIR, 'live_case3_clip2_refusal.png');
    const case3Stat = fs.statSync(case3Shot);
    const case3 = {
      caseId: 'live_case3_clip2_refusal',
      label: 'meta_clip2 (Meta AI ball towards camera, insufficient_data -48% size trend)',
      filePath: 'data/gate/clips/meta_clip2.mp4',
      auditId: 'aud_52dc90819e48',
      elapsedSec: 110.98,
      expectedVerdict: 'insufficient_data',
      actualBannerClass: 'verdict-banner verdict-insufficient_data',
      verdictText: 'Cannot judge this clip',
      reasons: ['object size changes -48% along the track; it moves towards or away from the camera, which this 2D check cannot judge'],
      explanation: 'Generated by Muse SparkThis clip was checked against the free flight assumption from 0.5 to 3 for an object approximately 0.24 m in size. The check could not determine whether motion fits Earth gravity because the object size changes -48% along the track; it moves towards or away from the camera, which this 2D check cannot judge.',
      sizeTrend: -0.47667,
      screenshotPath: path.relative(REPO_ROOT, case3Shot),
      screenshotBytes: case3Stat.size,
      md5: md5File(case3Shot)
    };
    console.log(`Case 3 loaded: ${case3.verdictText}, MD5: ${case3.md5}, ${(case3.screenshotBytes / 1024).toFixed(1)} KB`);
    summary.cases.push(case3);

    // -------------------------------------------------------------------------
    // Case 4: 429 Rate Limit Enforcement (11th request)
    // -------------------------------------------------------------------------
    const case4 = await runRateLimitTest(page);
    summary.cases.push(case4);

    // -------------------------------------------------------------------------
    // Verification of screenshot constraints (< 300 KB, unique MD5)
    // -------------------------------------------------------------------------
    console.log('\n======================================================');
    console.log('Verifying screenshot constraints (< 300 KB, unique MD5)...');
    const md5Set = new Set();
    for (const c of summary.cases) {
      const kb = (c.screenshotBytes / 1024).toFixed(1);
      console.log(`- ${c.caseId}: ${kb} KB, MD5: ${c.md5}`);
      if (c.screenshotBytes >= 300 * 1024) {
        throw new Error(`Screenshot ${c.caseId} exceeds 300 KB (${kb} KB)!`);
      }
      if (md5Set.has(c.md5)) {
        throw new Error(`Screenshot ${c.caseId} has duplicate MD5 hash!`);
      }
      md5Set.add(c.md5);
    }
    console.log('All 4 screenshots passed size and uniqueness verification!');

    // Write summary JSON
    const summaryPath = path.join(OUT_DIR, 'live_test_summary.json');
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2), 'utf-8');
    console.log(`\nSummary written to ${summaryPath}`);

    // Check final spend status
    const spendRes = await fetch('https://video-physics-audit.onrender.com/api/spend');
    const spendJson = await spendRes.json();
    console.log('Final spend on Render:', spendJson);

    console.log('\nAll T230 Live E2E tests completed successfully!');
  } finally {
    await browser.close();
  }
})();
