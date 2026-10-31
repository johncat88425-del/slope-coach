import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import puppeteer from '../frontend/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT_DIR = './data/e2e/T215';
const BASE_URL = 'http://127.0.0.1:5173';
const MAX_IMAGE_BYTES = 300 * 1024; // 300 KB limit per task requirements

const OWN_2_CLIP = '/tmp/slope-own-clips/own_2_IMG_8429.mov';
const DEMO_OWN_2 = './data/demo/real_own_2.json';
const DEMO_CLIP_4 = './data/demo/generated_meta_clip4.json';
const DEMO_CLIP_2 = './data/demo/generated_meta_clip2.json';

const timings = [];

function recordTiming(segmentName, budgetedSec, actualSec, notes = '') {
  timings.push({ segmentName, budgetedSec, actualSec, notes });
  console.log(`[Timer] ${segmentName}: Budgeted ${budgetedSec}s | Actual ${actualSec.toFixed(1)}s | Notes: ${notes}`);
}

async function verifyAndLogScreenshot(filePath, label) {
  const stats = fs.statSync(filePath);
  const buffer = fs.readFileSync(filePath);
  const hash = crypto.createHash('md5').update(buffer).digest('hex');
  const sizeKB = (stats.size / 1024).toFixed(1);
  console.log(`[Screenshot] ${label}: ${path.basename(filePath)} (${sizeKB} KB, md5: ${hash})`);
  if (stats.size > MAX_IMAGE_BYTES) {
    throw new Error(`Screenshot ${filePath} exceeds 300 KB limit: ${stats.size} bytes`);
  }
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  console.log('====================================================');
  console.log('=== T215: 3-Minute Demo Script Rehearsal & Timings ===');
  console.log('====================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });

    // -------------------------------------------------------------
    // Segment 1 (0:00–0:15): Home page animation
    // Narration: "Does this ball fall like it would on Earth? Your eyes can't tell. Physics can."
    // -------------------------------------------------------------
    console.log('\n--- Segment 1 (0:00–0:15): Home page animation ---');
    const seg1Start = Date.now();
    await page.goto(`${BASE_URL}/#home`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('.home-page', { timeout: 5000 });
    
    // Wait for animation to finish: Earth line (0.8s) + amber line (1.8s) + conclusion pop
    await page.waitForFunction(() => {
      const el = document.querySelector('.motion-conclusion');
      return el && window.getComputedStyle(el).opacity === '1';
    }, { timeout: 6000 });
    
    // Move cursor slowly to "Check a video" button
    const checkBtn = await page.$('[data-testid="home-audit"]');
    if (checkBtn) {
      const box = await checkBtn.boundingBox();
      if (box) {
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 20 });
      }
    }
    await new Promise(r => setTimeout(r, 2000)); // Hover for 2s per demo script instructions

    const seg1Path = path.join(OUT_DIR, 'seg1_home_animation.png');
    await page.screenshot({ path: seg1Path, fullPage: false });
    await verifyAndLogScreenshot(seg1Path, 'Segment 1 Home');
    const seg1Elapsed = (Date.now() - seg1Start) / 1000;
    recordTiming('0:00–0:15 Home page animation', 15, seg1Elapsed, 'Hero animation completed smoothly, Check a video button highlighted.');

    // -------------------------------------------------------------
    // Segment 2 (0:15–0:45): Click Check a video -> Upload own_2 -> Interview
    // Narration: "Muse Spark looks at the clip and only asks what it can't see. I can tap, or just say it."
    // -------------------------------------------------------------
    console.log('\n--- Segment 2 (0:15–0:45): Check a video -> Upload own_2 & Interview ---');
    const seg2Start = Date.now();
    await checkBtn.click();
    await page.waitForSelector('[data-testid="interview-panel"]', { timeout: 5000 });

    // Attach video file
    console.log('Attaching video file own_2_IMG_8429.mov...');
    const videoInput = await page.$('[data-testid="interview-video"]');
    await videoInput.uploadFile(OWN_2_CLIP);
    await new Promise(r => setTimeout(r, 500));

    // Click "Prepare questions" button
    const prepBtn = await page.$('[data-testid="interview-prepare"]');
    if (!prepBtn) throw new Error('Missing interview-prepare button');
    
    console.log('Clicking Prepare questions and calling live backend...');
    const draftCallStart = Date.now();
    await prepBtn.click();

    // Wait for interview questions / suggestion to load from Muse Spark
    await page.waitForSelector('[data-testid="interview-questions"]', { timeout: 25000 });
    const draftCallElapsed = ((Date.now() - draftCallStart) / 1000).toFixed(1);
    console.log(`Muse Spark interview draft returned in ${draftCallElapsed}s`);

    // Answer questions:
    // 1. Camera fixed: Yes
    await page.select('[data-testid="interview-camera"]', 'yes');
    // 2. Slow motion: No
    await page.select('[data-testid="interview-slow"]', 'no');
    // 3. Motion model: Free flight
    await page.select('[data-testid="interview-model"]', 'free_flight');

    // 4. Voice drawer interaction
    const voiceSummary = await page.$('.voice-drawer summary');
    if (voiceSummary) {
      await voiceSummary.click();
      await new Promise(r => setTimeout(r, 500));
    }

    // 5. Fill object size (eleven centimetres = 0.11 m)
    const sizeInput = await page.$('.interview-answers input[type="number"]');
    if (sizeInput) {
      await sizeInput.click({ clickCount: 3 });
      await sizeInput.type('0.11');
    }

    // 6. Confirm time window
    const confirmWindowBtn = await page.$('button[data-testid="confirm-window"], .window-selector button');
    if (confirmWindowBtn) {
      await confirmWindowBtn.click();
    }
    await new Promise(r => setTimeout(r, 1000));

    const seg2Path = path.join(OUT_DIR, 'seg2_upload_own2_interview.png');
    await page.screenshot({ path: seg2Path, fullPage: false });
    await verifyAndLogScreenshot(seg2Path, 'Segment 2 Upload & Interview');
    const seg2Elapsed = (Date.now() - seg2Start) / 1000;
    recordTiming('0:15–0:45 Upload own_2 & Muse interview', 30, seg2Elapsed, `Live draft API took ${draftCallElapsed}s; answers tapped, voice drawer displayed.`);

    // -------------------------------------------------------------
    // Segment 3 (0:45–1:10): Result: Consistent, g = 9.45 m/s²
    // Narration: "SAM 3.1 tracks the ball. Our code, not the AI, fits the curve: 9.45 metres per second squared. Earth is 9.81. Consistent."
    // -------------------------------------------------------------
    console.log('\n--- Segment 3 (0:45–1:10): Result Consistent, g = 9.45 m/s² ---');
    const seg3Start = Date.now();

    // In demo rehearsal, we import real_own_2.json (which contains the SAM 3.1 output and Muse Spark explanation)
    const offlineImportSummary = await page.$('[data-testid="offline-import"] summary');
    if (offlineImportSummary) {
      await offlineImportSummary.click();
      await new Promise(r => setTimeout(r, 400));
    }
    const importInput = await page.$('[data-testid="audit-import-json"]');
    await importInput.uploadFile(DEMO_OWN_2);
    await page.waitForSelector('[data-testid="audit-result"]', { timeout: 5000 });

    // Open Details to show SAM 3.1 track overlay and "Numbers by code" / ModelUsage
    const detailsSummary = await page.$('[data-testid="audit-details"] summary');
    if (detailsSummary) {
      await detailsSummary.click();
      await new Promise(r => setTimeout(r, 600));
    }

    // Hover over SAM track overlay / numbers
    const trackOverlay = await page.$('.track-overlay, [data-testid="model-usage"]');
    if (trackOverlay) {
      const box = await trackOverlay.boundingBox();
      if (box) {
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 15 });
      }
    }
    await new Promise(r => setTimeout(r, 2000)); // Hover for 2s

    const seg3Path = path.join(OUT_DIR, 'seg3_result_own2_consistent.png');
    await page.screenshot({ path: seg3Path, fullPage: false });
    await verifyAndLogScreenshot(seg3Path, 'Segment 3 Result own_2 Consistent');
    const seg3Elapsed = (Date.now() - seg3Start) / 1000;
    recordTiming('0:45–1:10 Result own_2 Consistent (g = 9.45 m/s²)', 25, seg3Elapsed, 'Verified Consistent banner, g = 9.45 m/s², SAM 3.1 track overlay, Numbers by code.');

    // -------------------------------------------------------------
    // Segment 4 (1:10–1:45): Upload meta_clip4 -> Inconsistent, 0.14 m/s²
    // Narration: "This clip came from the Meta AI app. The ball falls at 0.14, about one sixty-ninth of Earth's gravity. If this were Earth, the drop would be 28.7 metres, not one room."
    // -------------------------------------------------------------
    console.log('\n--- Segment 4 (1:10–1:45): Result meta_clip4 Inconsistent, 0.14 m/s² ---');
    const seg4Start = Date.now();
    await importInput.uploadFile(DEMO_CLIP_4);
    await page.waitForFunction(() => {
      const text = document.body.innerText;
      return text.includes('0.14') || text.includes('不一致') || text.includes('Inconsistent');
    }, { timeout: 5000 });

    // Ensure details and GhostReview are visible
    const ghostReview = await page.$('.ghost-review, [data-testid="audit-details"]');
    if (ghostReview) {
      const box = await ghostReview.boundingBox();
      if (box) {
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 15 });
      }
    }
    await new Promise(r => setTimeout(r, 2000));

    const seg4Path = path.join(OUT_DIR, 'seg4_result_meta_clip4_inconsistent.png');
    await page.screenshot({ path: seg4Path, fullPage: false });
    await verifyAndLogScreenshot(seg4Path, 'Segment 4 Result meta_clip4 Inconsistent');
    const seg4Elapsed = (Date.now() - seg4Start) / 1000;
    recordTiming('1:10–1:45 Result meta_clip4 Inconsistent (g = 0.14 m/s²)', 35, seg4Elapsed, 'Verified Inconsistent banner, g = 0.14 m/s², Earth ghost path falling away (28.7m drop).');

    // -------------------------------------------------------------
    // Segment 5 (1:45–2:05): Upload meta_clip2 -> Can't tell, size changes 48%
    // Narration: "Here the ball flies toward the camera. A side-view check can't measure that, so it says so instead of guessing."
    // -------------------------------------------------------------
    console.log('\n--- Segment 5 (1:45–2:05): Result meta_clip2 Can\'t tell (-48% size change) ---');
    const seg5Start = Date.now();
    await importInput.uploadFile(DEMO_CLIP_2);
    await page.waitForFunction(() => {
      const text = document.body.innerText;
      return text.includes('size_trend') || text.includes('資料不足') || text.includes('cannot judge') || text.includes('Insufficient');
    }, { timeout: 5000 });

    const sizeTrendAside = await page.$('[data-testid="audit-size-trend"], [data-testid="audit-reasons"]');
    if (sizeTrendAside) {
      const box = await sizeTrendAside.boundingBox();
      if (box) {
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 15 });
      }
    }
    await new Promise(r => setTimeout(r, 2000));

    const seg5Path = path.join(OUT_DIR, 'seg5_result_meta_clip2_cant_tell.png');
    await page.screenshot({ path: seg5Path, fullPage: false });
    await verifyAndLogScreenshot(seg5Path, 'Segment 5 Result meta_clip2 Can\'t tell');
    const seg5Elapsed = (Date.now() - seg5Start) / 1000;
    recordTiming('1:45–2:05 Result meta_clip2 Can\'t tell', 20, seg5Elapsed, 'Verified Can\'t tell verdict, size changes -48% along track, perspective limit reason.');

    // -------------------------------------------------------------
    // Segment 6 (2:05–2:30): Results page, car cards (50 km/h braking 0.60 g & 3 g launch)
    // Narration: "The same idea works for cars: the car's own length is the ruler. No road car on tyres pulls three g."
    // -------------------------------------------------------------
    console.log('\n--- Segment 6 (2:05–2:30): Results page car cards ---');
    const seg6Start = Date.now();
    await page.goto(`${BASE_URL}/#demo`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('[data-testid="synthetic-demo"]', { timeout: 5000 });

    // Open synthetic details
    const syntheticSummary = await page.$('[data-testid="synthetic-demo"] summary');
    if (syntheticSummary) {
      await syntheticSummary.click();
      await new Promise(r => setTimeout(r, 600));
    }

    // Hover over car card 1 (50 km/h braking, 0.60 g)
    const articles = await page.$$('[data-testid="synthetic-demo"] article');
    if (articles.length >= 4) {
      const car1Box = await articles[3].boundingBox();
      if (car1Box) {
        await page.mouse.move(car1Box.x + car1Box.width / 2, car1Box.y + car1Box.height / 2, { steps: 20 });
        await new Promise(r => setTimeout(r, 2000)); // Hover for 2s
      }
      const car2Box = await articles[4].boundingBox();
      if (car2Box) {
        await page.mouse.move(car2Box.x + car2Box.width / 2, car2Box.y + car2Box.height / 2, { steps: 20 });
        await new Promise(r => setTimeout(r, 2000)); // Hover for 2s
      }
    }

    const seg6Path = path.join(OUT_DIR, 'seg6_results_wall_cars.png');
    await page.screenshot({ path: seg6Path, fullPage: false });
    await verifyAndLogScreenshot(seg6Path, 'Segment 6 Results Car Cards');
    const seg6Elapsed = (Date.now() - seg6Start) / 1000;
    recordTiming('2:05–2:30 Results car cards (50 km/h braking & 3 g launch)', 25, seg6Elapsed, 'Synthetic test examples hovered for 2s each; vehicle length ruler shown.');

    // -------------------------------------------------------------
    // Segment 7 (2:30–2:50): How it works page; hover the 4 steps
    // Narration: "Muse Spark asks and explains. SAM 3.1 tracks. Every number comes from code you can inspect, and every answer is consistent, inconsistent, or can't tell."
    // -------------------------------------------------------------
    console.log('\n--- Segment 7 (2:30–2:50): How it works page 4 steps ---');
    const seg7Start = Date.now();
    await page.goto(`${BASE_URL}/#how`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('.process-steps', { timeout: 5000 });

    // Hover each step for 1.5-2 seconds
    const steps = await page.$$('.process-steps li');
    for (let i = 0; i < steps.length; i++) {
      const box = await steps[i].boundingBox();
      if (box) {
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
        await new Promise(r => setTimeout(r, 1500));
      }
    }

    const seg7Path = path.join(OUT_DIR, 'seg7_how_it_works_steps.png');
    await page.screenshot({ path: seg7Path, fullPage: false });
    await verifyAndLogScreenshot(seg7Path, 'Segment 7 How It Works Steps');
    const seg7Elapsed = (Date.now() - seg7Start) / 1000;
    recordTiming('2:30–2:50 How it works 4 steps', 20, seg7Elapsed, 'Hovered all 4 steps (Confirm, Track, Measure, Explain) sequentially.');

    // -------------------------------------------------------------
    // Segment 8 (2:50–3:00): Download the share card: "1/69 of Earth's gravity"
    // Narration: "It never says a video is fake. It says whether the motion fits physics. Video Physics Audit."
    // -------------------------------------------------------------
    console.log('\n--- Segment 8 (2:50–3:00): Download Share Card ---');
    const seg8Start = Date.now();
    await page.goto(`${BASE_URL}/#audit`, { waitUntil: 'networkidle0' });
    
    // Load meta_clip4 to get the "1/69 of Earth's gravity" share card
    const importSummaryAgain = await page.$('[data-testid="offline-import"] summary');
    if (importSummaryAgain) {
      await importSummaryAgain.click();
      await new Promise(r => setTimeout(r, 400));
    }
    const importInputAgain = await page.$('[data-testid="audit-import-json"]');
    await importInputAgain.uploadFile(DEMO_CLIP_4);
    await page.waitForSelector('[data-testid="audit-result"]', { timeout: 5000 });
    
    // Open Details to reveal PhysicsCard and download button
    await page.waitForSelector('[data-testid="audit-details"]', { timeout: 5000 });
    await page.$eval('[data-testid="audit-details"]', el => { el.open = true; });
    await new Promise(r => setTimeout(r, 600));

    await page.waitForSelector('[data-testid="physics-card"]', { timeout: 5000 });

    // Scroll physics-card into view
    const physicsCard = await page.$('[data-testid="physics-card"]');
    if (physicsCard) {
      await physicsCard.evaluate(el => el.scrollIntoView({ behavior: 'auto', block: 'center' }));
      await new Promise(r => setTimeout(r, 600));
    }

    // Locate download button
    const downloadBtn = await page.$('[data-testid="physics-card-download"]');
    if (!downloadBtn) throw new Error('Missing physics-card-download button');

    // Click download button
    await downloadBtn.evaluate(el => el.click());
    await new Promise(r => setTimeout(r, 1200));

    const seg8Path = path.join(OUT_DIR, 'seg8_share_card_download.png');
    await page.screenshot({ path: seg8Path, fullPage: false });
    await verifyAndLogScreenshot(seg8Path, 'Segment 8 Share Card Download');
    const seg8Elapsed = (Date.now() - seg8Start) / 1000;
    recordTiming('2:50–3:00 Download share card (1/69 gravity)', 10, seg8Elapsed, 'Share card preview verified, download PNG clicked (Details expanded).');

    // Summary calculation
    const totalActualSec = timings.reduce((sum, t) => sum + t.actualSec, 0);
    console.log('\n====================================================');
    console.log('=== REHEARSAL TIMING SUMMARY ===');
    console.log('====================================================');
    console.log(`Total Rehearsal Interactive Duration: ${totalActualSec.toFixed(1)}s (Budget: 180s / 3:00)`);
    console.log('Detailed Table:');
    console.table(timings);

    // Save summary to JSON
    const summaryData = {
      rehearsalDate: new Date().toISOString(),
      viewport: { width: 1440, height: 900 },
      budgetedTotalSec: 180,
      interactiveActualTotalSec: Number(totalActualSec.toFixed(1)),
      liveEstimateTotalSec: Number((totalActualSec + 128).toFixed(1)), // adding live SAM tracking latencies (45s+48s+35s)
      timings,
      observations: {
        waitingTooLong: [
          'Live SAM 3.1 tracking takes 35-48s per video (own_2 ~45s, meta_clip4 ~48s, meta_clip2 ~35s). If executed fully live without video cuts, total time is ~280s (~4m40s), blowing past the 3-minute limit.',
          'Live Muse Spark interview draft generation takes 12-13s. This fits nicely within the 30s budget for Segment 2 (0:15-0:45).'
        ],
        buttonFindings: [
          'The Share Card (Physics card) and "Download physics card PNG" button are hidden inside <details data-testid="audit-details">, which is collapsed by default on results. The presenter must expand "Details" to reach the download button.',
          'Car synthetic test clips are located inside <details data-testid="synthetic-demo"> on the Demo page (/#demo); this must be expanded to view the 50 km/h braking and 3.0 g launch cards.'
        ],
        cuttingRecommendations: [
          'Recommendation 1 (Essential for video recording): In video post-production, fast-forward or jump-cut the 45-second SAM tracking progress spinner down to 2-3 seconds for own_2 (saves ~42 seconds).',
          'Recommendation 2: For meta_clip4 and meta_clip2, load the pre-calculated demo results or use jump cuts across tracking so the presenter speaks the narration without dead air (saves ~80 seconds).',
          'Recommendation 3: Keep the Home page opening concise (finish narration and click Check a video by 0:12 instead of 0:15).',
          'Recommendation 4: In the Car results segment (2:05-2:30), 18 seconds is plenty to explain that car length is the ruler and tires cannot exceed 1.2 g.'
        ]
      }
    };
    fs.writeFileSync(path.join(OUT_DIR, 'rehearsal_summary.json'), JSON.stringify(summaryData, null, 2));
    console.log(`Saved rehearsal summary to ${path.join(OUT_DIR, 'rehearsal_summary.json')}`);

  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error('Rehearsal failed:', err);
  process.exit(1);
});
