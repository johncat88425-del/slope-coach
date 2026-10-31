import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import puppeteer from '/Users/aacc/Documents/slope-coach/frontend/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT_DIR = '/Users/aacc/Documents/slope-coach/data/e2e/T196';
const BASE_URL = 'http://127.0.0.1:5173';
const DEMO_JSON = '/Users/aacc/Documents/slope-coach/data/demo/real_own_2.json';
const MAX_IMAGE_BYTES = 300 * 1024; // 300 KB limit per task requirements

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  console.log('====================================================');
  console.log('=== T196 End-to-End Verification and Screenshots ===');
  console.log('====================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  const capturedFiles = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('[BROWSER CONSOLE ERROR]', msg.text());
    }
  });
  page.on('pageerror', err => {
    console.error('[BROWSER PAGE ERROR]', err);
  });

  async function saveScreenshot(filename, fullPage = false) {
    const filePath = path.join(OUT_DIR, filename);
    await page.screenshot({ path: filePath, fullPage });
    const stats = fs.statSync(filePath);
    const hash = crypto.createHash('md5').update(fs.readFileSync(filePath)).digest('hex');
    console.log(`Saved ${filename} (${(stats.size / 1024).toFixed(1)} KB, MD5: ${hash})`);
    if (stats.size > MAX_IMAGE_BYTES) {
      throw new Error(`File ${filename} exceeds 300 KB limit! Size: ${stats.size} bytes`);
    }
    capturedFiles.push({ filename, filePath, size: stats.size, hash });
  }

  // ==========================================
  // PART 1: Desktop Viewport (1440x900)
  // ==========================================
  console.log('\n--- PART 1: Desktop (1440x900) ---');
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });

  // 1.1 Home Page & Animation Verification
  console.log('\n1.1 Home page (#home)...');
  await page.goto(`${BASE_URL}/#home`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('[data-testid="home-motion"]');

  console.log('Waiting for Home animation keyframes (3.8s)...');
  await new Promise(r => setTimeout(r, 3800));

  const anim = await page.evaluate(() => {
    const earth = document.querySelector('.hero-earth');
    const obs = document.querySelector('.hero-observed');
    const ep = document.querySelector('.hero-endpoint');
    const conc = document.querySelector('.motion-conclusion');
    return {
      hasEarth: !!earth,
      hasObserved: !!obs,
      hasEndpoint: !!ep,
      conclusionText: conc ? conc.textContent.trim() : '',
      conclusionOpacity: conc ? window.getComputedStyle(conc).opacity : '0',
      observedStrokeOffset: obs ? window.getComputedStyle(obs).strokeDashoffset : ''
    };
  });
  console.log('Home animation verification:', anim);
  if (!anim.hasEarth || !anim.hasObserved || !anim.hasEndpoint) {
    throw new Error('Home animation elements missing!');
  }
  if (!anim.conclusionText.includes("Doesn't match Earth gravity")) {
    throw new Error(`Home conclusion text unexpected: "${anim.conclusionText}"`);
  }
  await saveScreenshot('home_1440px.png');

  // 1.2 Results Wall Page (#wall)
  console.log('\n1.2 Results page (#wall)...');
  await page.goto(`${BASE_URL}/#wall`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('[data-testid="results-wall"]');
  await new Promise(r => setTimeout(r, 600));
  await saveScreenshot('results_1440px.png');

  // 1.3 Results Wall: Hover Interaction Verification
  console.log('\n1.3 Results page card hover interaction...');
  const cards = await page.$$('[data-testid="opening-card"]');
  if (cards.length < 3) throw new Error(`Expected at least 3 opening cards, found ${cards.length}`);
  
  await cards[0].hover();
  await new Promise(r => setTimeout(r, 600));

  const hoverVerification = await page.evaluate(() => {
    const cardElements = Array.from(document.querySelectorAll('[data-testid="opening-card"]'));
    return cardElements.map((card, idx) => {
      const style = window.getComputedStyle(card);
      const ev = card.querySelector('.preview-evidence');
      const evStyle = ev ? window.getComputedStyle(ev) : null;
      return {
        idx,
        transform: style.transform,
        opacity: style.opacity,
        filter: style.filter,
        evidenceOpacity: evStyle ? evStyle.opacity : null,
        evidenceText: ev ? ev.textContent.trim() : null
      };
    });
  });
  console.log('Results hover verification:', hoverVerification);
  if (!hoverVerification[0].transform.includes('1.05')) {
    console.warn('Warning: Active card transform does not include 1.05 scale:', hoverVerification[0].transform);
  }
  if (hoverVerification[1].opacity !== '0.45' || !hoverVerification[1].filter.includes('blur')) {
    console.warn('Warning: Sibling card does not exhibit dimming/blur:', hoverVerification[1]);
  }
  await saveScreenshot('results_card_hover_1440px.png');

  // 1.4 How It Works Page (#how)
  console.log('\n1.4 How it works page (#how)...');
  await page.goto(`${BASE_URL}/#how`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('[data-testid="how-it-works"]');

  const steps = await page.$$('.process-steps > li');
  if (steps.length > 0) {
    await steps[0].hover();
    await new Promise(r => setTimeout(r, 400));
  }
  await saveScreenshot('how_1440px.png');

  // 1.5 Upload / Audit Page (#audit)
  console.log('\n1.5 Upload / Audit page (#audit)...');
  await page.goto(`${BASE_URL}/#audit`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('.audit-flow');
  await new Promise(r => setTimeout(r, 500));
  await saveScreenshot('audit_1440px.png');

  // 1.6 Replay / Upload Saved Case from data/demo
  console.log('\n1.6 Uploading / Replaying data/demo/real_own_2.json on #audit...');
  await page.evaluate(() => {
    const details = document.querySelector('[data-testid="offline-import"]');
    if (details) details.open = true;
  });
  await new Promise(r => setTimeout(r, 200));

  const importInput = await page.$('[data-testid="audit-import-json"]');
  if (!importInput) throw new Error('Offline import input not found!');
  await importInput.uploadFile(DEMO_JSON);

  await page.waitForSelector('[data-testid="audit-result"]');
  const importedVerdict = await page.$eval('[data-testid="audit-verdict"]', el => el.textContent.trim());
  console.log('Imported audit result verdict:', importedVerdict);
  if (!importedVerdict.includes('Consistent')) {
    throw new Error(`Unexpected imported verdict: ${importedVerdict}`);
  }
  await new Promise(r => setTimeout(r, 500));
  await saveScreenshot('audit_result_imported_1440px.png');

  // 1.7 Language Switching Test
  console.log('\n1.7 Language switching test (EN -> ZH -> EN)...');
  await page.goto(`${BASE_URL}/#home`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('[data-testid="nav-wall"]');

  // Switch to ZH
  await page.select('select[aria-label="Language / 語言"]', 'zh');
  await new Promise(r => setTimeout(r, 500));
  const zhNavText = await page.$eval('[data-testid="nav-wall"]', el => el.textContent.trim());
  console.log('Language switched to ZH, Nav text:', zhNavText);
  if (!zhNavText.includes('結果')) {
    throw new Error(`Expected Chinese translation for Nav, got "${zhNavText}"`);
  }
  await saveScreenshot('home_zh_1440px.png');

  // Switch back to EN
  await page.select('select[aria-label="Language / 語言"]', 'en');
  await new Promise(r => setTimeout(r, 500));
  const enNavText = await page.$eval('[data-testid="nav-wall"]', el => el.textContent.trim());
  console.log('Language switched back to EN, Nav text:', enNavText);
  if (!enNavText.includes('Results')) {
    throw new Error(`Expected English for Nav, got "${enNavText}"`);
  }

  // 1.8 Keyboard Navigation Test (Tab & Enter)
  console.log('\n1.8 Keyboard navigation test (Tab & Enter)...');
  await page.goto(`${BASE_URL}/#home`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('[data-testid="nav-wall"]');
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    document.body.focus();
  });

  // Tab until reaching Results link
  let focusedResults = false;
  for (let i = 0; i < 10; i++) {
    await page.keyboard.press('Tab');
    const href = await page.evaluate(() => document.activeElement?.getAttribute('href'));
    if (href === '#wall') {
      focusedResults = true;
      break;
    }
  }
  console.log('Focused #wall link via Tab:', focusedResults);

  // Press Enter to navigate to #wall
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => location.hash === '#wall');
  console.log('Navigated via keyboard Enter to:', await page.evaluate(() => location.hash));

  // On #wall, tab until reaching first opening card
  let focusedCard = false;
  for (let i = 0; i < 10; i++) {
    await page.keyboard.press('Tab');
    const verdict = await page.evaluate(() => document.activeElement?.getAttribute('data-verdict'));
    if (verdict) {
      focusedCard = true;
      console.log('Focused opening card via Tab:', verdict);
      break;
    }
  }
  await saveScreenshot('keyboard_nav_1440px.png');

  // ==========================================
  // PART 2: Mobile Viewport (390x844)
  // ==========================================
  console.log('\n--- PART 2: Mobile (390x844) ---');
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });

  // 2.1 Mobile Home
  console.log('\n2.1 Mobile Home (#home)...');
  await page.goto(`${BASE_URL}/#home`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('[data-testid="home-motion"]');
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('home_390px.png');

  // 2.2 Mobile Results (#wall)
  console.log('\n2.2 Mobile Results (#wall)...');
  await page.goto(`${BASE_URL}/#wall`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('[data-testid="results-wall"]');
  await new Promise(r => setTimeout(r, 600));
  await saveScreenshot('results_390px.png');

  // 2.3 Mobile How It Works (#how)
  console.log('\n2.3 Mobile How it works (#how)...');
  await page.goto(`${BASE_URL}/#how`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('[data-testid="how-it-works"]');
  await new Promise(r => setTimeout(r, 600));
  await saveScreenshot('how_390px.png');

  // 2.4 Mobile Upload / Audit (#audit)
  console.log('\n2.4 Mobile Upload / Audit (#audit)...');
  await page.goto(`${BASE_URL}/#audit`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('.audit-flow');
  await new Promise(r => setTimeout(r, 600));
  await saveScreenshot('audit_390px.png');

  // 2.5 Mobile Audit Result Imported
  console.log('\n2.5 Mobile Audit Result Imported (#audit)...');
  await page.evaluate(() => {
    const details = document.querySelector('[data-testid="offline-import"]');
    if (details) details.open = true;
  });
  await new Promise(r => setTimeout(r, 200));

  const mobInput = await page.$('[data-testid="audit-import-json"]');
  await mobInput.uploadFile(DEMO_JSON);
  await page.waitForSelector('[data-testid="audit-result"]');
  await new Promise(r => setTimeout(r, 500));
  await saveScreenshot('audit_result_imported_390px.png');

  await browser.close();

  // ==========================================
  // Summary & Size Verification
  // ==========================================
  console.log('\n====================================================');
  console.log('=== SUMMARY OF CAPTURED SCREENSHOTS ===');
  console.log('====================================================');
  let allUnderLimit = true;
  for (const item of capturedFiles) {
    const pass = item.size <= MAX_IMAGE_BYTES;
    if (!pass) allUnderLimit = false;
    console.log(`- ${item.filename.padEnd(32)}: ${(item.size / 1024).toFixed(1).padStart(6)} KB  [${pass ? 'PASS' : 'FAIL >300KB'}]  MD5: ${item.hash}`);
  }

  if (!allUnderLimit) {
    throw new Error('Some screenshots exceeded the 300 KB limit!');
  }
  console.log('\nSUCCESS: All screenshots verified under 300 KB and captured successfully!\n');
}

main().catch(err => {
  console.error('\nE2E SCRIPT FAILED:', err);
  process.exit(1);
});
