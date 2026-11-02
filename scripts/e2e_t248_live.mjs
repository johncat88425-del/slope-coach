import puppeteer from '../frontend/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..');
const LIVE_URL = 'https://video-physics-audit.onrender.com/#audit';
const OUT_DIR = path.resolve(REPO_ROOT, 'data/e2e/T248');

fs.mkdirSync(OUT_DIR, { recursive: true });

function md5File(filepath) {
  const buf = fs.readFileSync(filepath);
  return crypto.createHash('md5').update(buf).digest('hex');
}

async function setInputValue(page, selector, value) {
  await page.waitForSelector(selector, { timeout: 30000 });
  await page.evaluate((sel, val) => {
    const el = document.querySelector(sel);
    if (!el) throw new Error(`Selector not found: ${sel}`);
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(el, val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }, selector, value);
}

async function setSelectValue(page, selector, value) {
  await page.waitForSelector(selector, { timeout: 30000 });
  await page.select(selector, value);
}

async function setMeasuredSize(page, value) {
  await page.evaluate((val) => {
    const labels = Array.from(document.querySelectorAll('label'));
    const sizeLabel = labels.find(l => l.textContent.includes('Measured object size') || l.textContent.includes('Car body length'));
    const input = sizeLabel ? sizeLabel.querySelector('input') : null;
    if (input) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(input, val);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }, String(value));
}

async function waitForVideoDuration(page, minDuration = 0.1) {
  await page.waitForFunction(
    (minD) => {
      const v = document.querySelector('video');
      return v && Number.isFinite(v.duration) && v.duration >= minD;
    },
    { timeout: 30000 },
    minDuration
  );
}

async function setAndConfirmWindow(page, startVal, endVal) {
  console.log(`Setting time window: ${startVal}s -> ${endVal}s...`);
  await page.waitForSelector('input[data-testid="window-start"]', { timeout: 30000 });
  await setInputValue(page, 'input[data-testid="window-start"]', String(startVal));
  await setInputValue(page, 'input[data-testid="window-end"]', String(endVal));
  await new Promise(r => setTimeout(r, 600));

  const confirmBtn = await page.$('button[data-testid="window-confirm"]');
  if (!confirmBtn) throw new Error('Confirm window button not found');
  await confirmBtn.click();

  await page.waitForFunction(() => {
    const b = document.querySelector('button[data-testid="window-confirm"]');
    return b && b.textContent.includes('confirmed');
  }, { timeout: 15000 });
  console.log('Window confirmed successfully.');
}

async function waitForAuditResult(page, timeoutMs = 420000) {
  const start = Date.now();
  let lastLogged = start;
  while (Date.now() - start < timeoutMs) {
    const hasVerdict = (await page.$('[data-testid="audit-verdict"]')) !== null;
    const hasError = (await page.$('[data-testid="audit-error"], .api-error-notice[role="alert"]')) !== null;
    if (hasVerdict || hasError) {
      return Number(((Date.now() - start) / 1000).toFixed(2));
    }
    await new Promise(r => setTimeout(r, 2000));
    if (Date.now() - lastLogged >= 15000) {
      const sec = Math.round((Date.now() - start) / 1000);
      console.log(`  ...still polling /api/audit-jobs (${sec}s elapsed)`);
      lastLogged = Date.now();
    }
  }
  throw new Error(`Audit result timed out after ${timeoutMs / 1000}s`);
}

async function extractResultData(page) {
  return await page.evaluate(() => {
    const verdictEl = document.querySelector('[data-testid="audit-verdict"]');
    const reasonsEl = document.querySelectorAll('[data-testid="audit-reasons"] li');
    const explanationEl = document.querySelector('[data-testid="audit-explanation"]');
    const banner = document.querySelector('.verdict-banner');
    const headline = document.querySelector('[data-testid="model-headline"]');
    const errEl = document.querySelector('[data-testid="audit-error"]') || document.querySelector('[role="alert"]');
    const rulerP = Array.from(document.querySelectorAll('figure[data-testid="gravity-ruler"] p')).find(p => p.textContent.includes('Estimated gravity:'));
    const detailsP = Array.from(document.querySelectorAll('[data-testid="audit-details"] p')).map(p => p.textContent.trim());

    let apparentG = null;
    if (rulerP) {
      const match = rulerP.textContent.match(/Estimated gravity:\s*([\d\.]+)/);
      if (match) apparentG = Number(match[1]);
    }
    if (apparentG === null) {
      const text = Array.from(reasonsEl).map(li => li.textContent).join(' ');
      const m = text.match(/apparent g\s*([\d\.]+)/i) || text.match(/g\s*=\s*([\d\.]+)/i);
      if (m) apparentG = Number(m[1]);
    }

    return {
      verdictText: verdictEl ? verdictEl.textContent.trim() : '',
      bannerClass: banner ? banner.className : '',
      apparentG,
      gravityRulerText: rulerP ? rulerP.textContent.trim() : null,
      reasons: Array.from(reasonsEl).map(li => li.textContent.trim()),
      limits: detailsP,
      explanation: explanationEl ? explanationEl.textContent.trim() : '',
      headline: headline ? headline.textContent.trim() : '',
      errorText: errEl ? errEl.textContent.trim() : ''
    };
  });
}

async function captureResultScreenshot(page, outFilename) {
  const outPath = path.join(OUT_DIR, outFilename);
  await page.evaluate(() => {
    const res = document.querySelector('[data-testid="audit-result"]') ||
                document.querySelector('[data-testid="audit-error"]') ||
                document.querySelector('article') ||
                document.querySelector('.audit-result-group');
    if (res) res.scrollIntoView({ behavior: 'instant', block: 'start' });
  });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: outPath, fullPage: false });
  const stat = fs.statSync(outPath);
  console.log(`Saved screenshot: ${outFilename} (${(stat.size / 1024).toFixed(1)} KB)`);
  return {
    path: path.relative(REPO_ROOT, outPath),
    bytes: stat.size,
    md5: md5File(outPath)
  };
}

// -----------------------------------------------------------------------------
// Case 1: meta_ai_ball_4 (Sample clip)
// -----------------------------------------------------------------------------
async function runCase1(page) {
  console.log('\n======================================================');
  console.log('[Case 1] Sample Clip: meta_ai_ball_4 (Meta AI basketball)');
  console.log('Expected: verdict = inconsistent, g ≈ 0.14 m/s²');

  await page.goto(LIVE_URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('button[data-testid="try-sample"]', { timeout: 30000 });

  console.log('Clicking "Try a sample clip"...');
  await page.click('button[data-testid="try-sample"]');

  console.log('Waiting for sample options...');
  await page.waitForSelector('button[data-testid="choose-sample"]', { timeout: 30000 });

  const chosen = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button[data-testid="choose-sample"]'));
    const b = btns.find(el => el.textContent.includes('Meta AI') || el.textContent.includes('meta_ai_ball_4') || el.textContent.includes('Ball clip'));
    if (b) {
      b.click();
      return b.textContent.trim();
    }
    return null;
  });
  console.log('Selected sample:', chosen);

  console.log('Waiting for draft preparation & window selector...');
  await page.waitForSelector('section[data-testid="window-selector"]', { timeout: 90000 });
  await waitForVideoDuration(page, 1.0);

  // Set window: 0.0 to 2.5
  await setAndConfirmWindow(page, '0.0', '2.5');

  // Answers
  console.log('Filling interview questions...');
  await setSelectValue(page, 'select[data-testid="interview-camera"]', 'yes');
  await setSelectValue(page, 'select[data-testid="interview-slow"]', 'no');
  await setSelectValue(page, 'select[data-testid="interview-model"]', 'free_flight');
  await setMeasuredSize(page, '0.24');

  console.log('Submitting audit check via interview panel...');
  await page.click('button[data-testid="interview-submit"]');

  console.log('Waiting for audit verdict (polling audit-jobs)...');
  const elapsedSec = await waitForAuditResult(page, 420000);
  const resultData = await extractResultData(page);

  console.log(`[Case 1] Finished in ${elapsedSec}s:`, resultData);
  const shot = await captureResultScreenshot(page, 't248_case1_meta_ai_ball_4.png');

  return {
    caseId: 'case1_meta_ai_ball_4',
    name: 'Sample: meta_ai_ball_4 (Meta AI basketball)',
    elapsedSec,
    resultData,
    screenshot: shot
  };
}

// -----------------------------------------------------------------------------
// Case 2: synthetic_toss (Sample clip)
// -----------------------------------------------------------------------------
async function runCase2(page) {
  console.log('\n======================================================');
  console.log('[Case 2] Sample Clip: synthetic_toss (Code-drawn Earth toss)');
  console.log('Expected: verdict = consistent');

  await page.goto(LIVE_URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('button[data-testid="try-sample"]', { timeout: 30000 });

  console.log('Clicking "Try a sample clip"...');
  await page.click('button[data-testid="try-sample"]');

  await page.waitForSelector('button[data-testid="choose-sample"]', { timeout: 30000 });

  const chosen = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button[data-testid="choose-sample"]'));
    const b = btns.find(el => el.textContent.includes('Synthetic test clip') || el.textContent.includes('synthetic_toss') || el.textContent.includes('6 cm square'));
    if (b) {
      b.click();
      return b.textContent.trim();
    }
    return null;
  });
  console.log('Selected sample:', chosen);

  console.log('Waiting for draft preparation & window selector...');
  await page.waitForSelector('section[data-testid="window-selector"]', { timeout: 90000 });
  await waitForVideoDuration(page, 0.5);

  // Set window: 0.0 to 0.6
  await setAndConfirmWindow(page, '0.0', '0.6');

  console.log('Filling interview questions...');
  await setSelectValue(page, 'select[data-testid="interview-camera"]', 'yes');
  await setSelectValue(page, 'select[data-testid="interview-slow"]', 'no');
  await setSelectValue(page, 'select[data-testid="interview-model"]', 'free_flight');
  await setMeasuredSize(page, '0.06');

  console.log('Submitting audit check via interview panel...');
  await page.click('button[data-testid="interview-submit"]');

  console.log('Waiting for audit verdict (polling audit-jobs)...');
  const elapsedSec = await waitForAuditResult(page, 420000);
  const resultData = await extractResultData(page);

  console.log(`[Case 2] Finished in ${elapsedSec}s:`, resultData);
  const shot = await captureResultScreenshot(page, 't248_case2_synthetic_toss.png');

  return {
    caseId: 'case2_synthetic_toss',
    name: 'Sample: synthetic_toss (Code-drawn Earth toss)',
    elapsedSec,
    resultData,
    screenshot: shot
  };
}

// -----------------------------------------------------------------------------
// Case 3: Pexels Real Basketball Clip (Handheld camera / "鏡頭沒固定")
// -----------------------------------------------------------------------------
async function runCase3(page) {
  console.log('\n======================================================');
  console.log('[Case 3] Real clip: Pexels pexels_basketball_arc.mp4');
  console.log('Condition: camera answered "not fixed" (沒固定), window: 0.64–1.28s');
  console.log('Expected: consistent, g ≈ 10.6 m/s² (camera shake compensated)');

  const videoPath = '/Users/aacc/Downloads/pexels_basketball_arc.mp4';
  if (!fs.existsSync(videoPath)) throw new Error(`File not found: ${videoPath}`);

  await page.goto(LIVE_URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('input[data-testid="interview-video"]', { timeout: 30000 });

  console.log('Uploading pexels_basketball_arc.mp4...');
  const fileInput = await page.$('input[data-testid="interview-video"]');
  await fileInput.uploadFile(videoPath);

  await page.waitForSelector('button[data-testid="interview-prepare"]', { timeout: 10000 });
  await page.click('button[data-testid="interview-prepare"]');

  console.log('Waiting for draft preparation & window selector...');
  await page.waitForSelector('section[data-testid="window-selector"]', { timeout: 90000 });
  await waitForVideoDuration(page, 2.0);

  // Time window: 0.64 to 1.28s
  await setAndConfirmWindow(page, '0.64', '1.28');

  // Camera answered "not fixed" -> 'no'
  console.log('Filling interview questions (camera = "no")...');
  await setSelectValue(page, 'select[data-testid="interview-camera"]', 'no');
  await setSelectValue(page, 'select[data-testid="interview-slow"]', 'no');
  await setSelectValue(page, 'select[data-testid="interview-model"]', 'free_flight');

  // Object name basketball
  await setInputValue(page, 'input[data-testid="interview-object-name"]', 'basketball');
  await setMeasuredSize(page, '0.24');

  console.log('Submitting audit check via interview panel...');
  await page.click('button[data-testid="interview-submit"]');

  console.log('Waiting for audit verdict (polling audit-jobs)...');
  const elapsedSec = await waitForAuditResult(page, 420000);
  const resultData = await extractResultData(page);

  console.log(`[Case 3] Finished in ${elapsedSec}s:`, resultData);
  const shot = await captureResultScreenshot(page, 't248_case3_pexels_basketball.png');

  return {
    caseId: 'case3_pexels_basketball',
    name: 'Pexels pexels_basketball_arc.mp4 (camera=no, window 0.64-1.28s)',
    elapsedSec,
    resultData,
    screenshot: shot
  };
}

// -----------------------------------------------------------------------------
// Case 4: 4K UHD Clip (Must not crash the server)
// -----------------------------------------------------------------------------
async function runCase4(page) {
  console.log('\n======================================================');
  console.log('[Case 4] 4K UHD clip: 4064324-uhd_3840_2160_25fps.mp4');
  console.log('Requirement: Server scales down without crashing or OOM');

  const videoPath = '/Users/aacc/Downloads/4064324-uhd_3840_2160_25fps.mp4';
  if (!fs.existsSync(videoPath)) throw new Error(`File not found: ${videoPath}`);

  await page.goto(LIVE_URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('input[data-testid="interview-video"]', { timeout: 30000 });

  console.log('Uploading 4K clip (23.3 MB)...');
  const fileInput = await page.$('input[data-testid="interview-video"]');
  await fileInput.uploadFile(videoPath);

  await page.waitForSelector('button[data-testid="interview-prepare"]', { timeout: 10000 });
  await page.click('button[data-testid="interview-prepare"]');

  console.log('Waiting for draft preparation & window selector (shrinks to 1920)...');
  await page.waitForSelector('section[data-testid="window-selector"]', { timeout: 240000 });
  await waitForVideoDuration(page, 2.0);

  // Time window: 1.0 to 2.0s
  await setAndConfirmWindow(page, '1.0', '2.0');

  console.log('Filling interview questions...');
  await setSelectValue(page, 'select[data-testid="interview-camera"]', 'yes');
  await setSelectValue(page, 'select[data-testid="interview-slow"]', 'no');
  await setSelectValue(page, 'select[data-testid="interview-model"]', 'vehicle');
  await setSelectValue(page, 'select[data-testid="vehicle-class"]', 'unknown');
  await setInputValue(page, 'input[data-testid="interview-object-name"]', 'car');

  console.log('Submitting audit check via interview panel...');
  await page.click('button[data-testid="interview-submit"]');

  console.log('Waiting for audit verdict or response...');
  const elapsedSec = await waitForAuditResult(page, 600000);
  const resultData = await extractResultData(page);

  console.log(`[Case 4] Finished in ${elapsedSec}s:`, resultData);
  const shot = await captureResultScreenshot(page, 't248_case4_4k_clip.png');

  return {
    caseId: 'case4_4k_clip',
    name: '4K Clip 4064324-uhd_3840_2160_25fps.mp4',
    elapsedSec,
    resultData,
    screenshot: shot
  };
}

// -----------------------------------------------------------------------------
// Case 5: 5-Second Time Window Clip (> 2 minutes background jobs verification)
// -----------------------------------------------------------------------------
async function runCase5(page) {
  console.log('\n======================================================');
  console.log('[Case 5] 5-Second Window: pexels_basketball_arc.mp4 (window 0.0–5.0s)');
  console.log('Requirement: Downsamples frames, tests background jobs polling > 2 min without timeout');

  const videoPath = '/Users/aacc/Downloads/pexels_basketball_arc.mp4';
  if (!fs.existsSync(videoPath)) throw new Error(`File not found: ${videoPath}`);

  await page.goto(LIVE_URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('input[data-testid="interview-video"]', { timeout: 30000 });

  console.log('Uploading pexels_basketball_arc.mp4 for 5-second window test...');
  const fileInput = await page.$('input[data-testid="interview-video"]');
  await fileInput.uploadFile(videoPath);

  await page.waitForSelector('button[data-testid="interview-prepare"]', { timeout: 10000 });
  await page.click('button[data-testid="interview-prepare"]');

  console.log('Waiting for draft preparation & window selector...');
  await page.waitForSelector('section[data-testid="window-selector"]', { timeout: 90000 });
  await waitForVideoDuration(page, 4.0);

  // Time window: 0.0 to 5.0s (Full 5 seconds!)
  await setAndConfirmWindow(page, '0.0', '5.0');

  console.log('Filling interview questions...');
  await setSelectValue(page, 'select[data-testid="interview-camera"]', 'no');
  await setSelectValue(page, 'select[data-testid="interview-slow"]', 'no');
  await setSelectValue(page, 'select[data-testid="interview-model"]', 'free_flight');
  await setInputValue(page, 'input[data-testid="interview-object-name"]', 'basketball');
  await setMeasuredSize(page, '0.24');

  console.log('Submitting audit check (long 5s window)...');
  await page.click('button[data-testid="interview-submit"]');

  console.log('Waiting for background job completion (polling /api/audit-jobs every 3s)...');
  const elapsedSec = await waitForAuditResult(page, 600000);
  const resultData = await extractResultData(page);

  console.log(`[Case 5] Finished in ${elapsedSec}s:`, resultData);
  const shot = await captureResultScreenshot(page, 't248_case5_5s_window.png');

  return {
    caseId: 'case5_5s_window',
    name: 'pexels_basketball_arc.mp4 5-second window (0.0-5.0s)',
    elapsedSec,
    resultData,
    screenshot: shot
  };
}

// -----------------------------------------------------------------------------
// Main Runner
// -----------------------------------------------------------------------------
(async () => {
  const targetCase = process.argv[2] || 'all';
  console.log('======================================================');
  console.log('Starting T248 Live E2E Audit Verification');
  console.log(`Target: ${LIVE_URL} (Selection: ${targetCase})`);
  console.log('======================================================');

  // 1. Verify commit version
  console.log('Checking /api/version...');
  const vRes = await fetch('https://video-physics-audit.onrender.com/api/version');
  const vJson = await vRes.json();
  console.log('Live server version:', vJson);

  const summaryFile = path.join(OUT_DIR, 't248_summary.json');
  let summary = {
    testDate: new Date().toISOString(),
    liveUrl: LIVE_URL,
    liveCommit: vJson.commit,
    cases: []
  };

  if (fs.existsSync(summaryFile)) {
    try {
      summary = JSON.parse(fs.readFileSync(summaryFile, 'utf-8'));
    } catch {}
  }

  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    protocolTimeout: 600000,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // Console listener to see frontend job polling logs
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('audit-jobs') || text.includes('poll') || text.includes('error') || text.includes('Error')) {
      console.log(`[Browser Console ${msg.type()}]:`, text);
    }
  });

  try {
    if (targetCase === 'all' || targetCase === 'case1') {
      const c1 = await runCase1(page);
      summary.cases = summary.cases.filter(c => c.caseId !== c1.caseId).concat(c1);
      fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
    }
    if (targetCase === 'all' || targetCase === 'case2') {
      const c2 = await runCase2(page);
      summary.cases = summary.cases.filter(c => c.caseId !== c2.caseId).concat(c2);
      fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
    }
    if (targetCase === 'all' || targetCase === 'case3') {
      const c3 = await runCase3(page);
      summary.cases = summary.cases.filter(c => c.caseId !== c3.caseId).concat(c3);
      fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
    }
    if (targetCase === 'all' || targetCase === 'case4') {
      const c4 = await runCase4(page);
      summary.cases = summary.cases.filter(c => c.caseId !== c4.caseId).concat(c4);
      fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
    }
    if (targetCase === 'all' || targetCase === 'case5') {
      const c5 = await runCase5(page);
      summary.cases = summary.cases.filter(c => c.caseId !== c5.caseId).concat(c5);
      fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
    }

    // Verify screenshot sizes (< 300 KB) and uniqueness (unique MD5)
    console.log('\n======================================================');
    console.log('Verifying screenshot constraints (< 300 KB, unique MD5)...');
    const md5Set = new Set();
    for (const c of summary.cases) {
      const kb = (c.screenshot.bytes / 1024).toFixed(1);
      console.log(`- ${c.caseId}: ${kb} KB, MD5: ${c.screenshot.md5}`);
      if (c.screenshot.bytes >= 300 * 1024) {
        throw new Error(`Screenshot for ${c.caseId} exceeds 300 KB (${kb} KB)!`);
      }
      if (md5Set.has(c.screenshot.md5)) {
        throw new Error(`Screenshot for ${c.caseId} has duplicate MD5 hash!`);
      }
      md5Set.add(c.screenshot.md5);
    }
    console.log('Screenshots verified (< 300 KB, all MD5 unique)!');

    // Final spend status
    const spendRes = await fetch('https://video-physics-audit.onrender.com/api/spend');
    const spendJson = await spendRes.json();
    console.log('Final spend status:', spendJson);

    console.log('\nT248 E2E Live Audit run step finished.');
  } catch (err) {
    console.error('\nE2E Test encountered an error:', err);
    try {
      const errShot = path.join(OUT_DIR, 'error_state.png');
      await page.screenshot({ path: errShot });
      console.log('Saved error screenshot to:', errShot);
    } catch {}
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
