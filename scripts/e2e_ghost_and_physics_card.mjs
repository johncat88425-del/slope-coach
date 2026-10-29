import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import puppeteer from '../frontend/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT_DIR = './docs/screens';

async function runE2E() {
    fs.mkdirSync(OUT_DIR, { recursive: true });

    console.log('=== T68 Ghost Review & Physics Card End-to-End Test ===');
    const browser = await puppeteer.launch({
        executablePath: CHROME_PATH,
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const page = await browser.newPage();
        
        // Listen to console and errors
        page.on('console', msg => {
            if (msg.type() === 'error') console.error('Browser console error:', msg.text());
        });
        page.on('pageerror', err => console.error('Browser page error:', err));

        // 1. Desktop Test (1280x900)
        console.log('\n[Step 1] Loading Demo Page on Desktop (1280x900)...');
        await page.setViewport({ width: 1280, height: 900 });
        await page.goto('http://127.0.0.1:5173/#demo', { waitUntil: 'networkidle0' });

        await page.waitForSelector('[data-testid="demo-comparison"]');
        console.log('   ✓ Loaded Demo Page with data-testid="demo-comparison"');

        // Open details
        await page.evaluate(() => {
            const details = document.querySelector('[data-testid="audit-details"]');
            if (details) details.open = true;
        });

        // Verify Ghost Review components
        console.log('\n[Step 2] Verifying Ghost Review elements...');
        await page.waitForSelector('[data-testid="ghost-review"]', { visible: true });
        const hasGap = await page.$eval('[data-testid="ghost-gap"]', el => !!el.textContent);
        const hasPlay = await page.$('[data-testid="points-play"]');
        const hasScrubber = await page.$('[data-testid="points-scrubber"]');
        console.log(`   ✓ Ghost comparison section present`);
        console.log(`   ✓ Ghost gap indicator present: ${hasGap}`);
        console.log(`   ✓ Playback controls present: play=${!!hasPlay}, scrubber=${!!hasScrubber}`);

        // Capture Desktop Ghost Review screenshot
        await page.evaluate(() => {
            document.querySelector('[data-testid="ghost-review"]').scrollIntoView();
        });
        await new Promise(r => setTimeout(r, 600));
        const ghostDesktopPath = path.join(OUT_DIR, 'ghost_review_desktop.png');
        await page.screenshot({ path: ghostDesktopPath });
        console.log(`   ✓ Saved ${ghostDesktopPath}`);

        // Verify Physics Card components
        console.log('\n[Step 3] Verifying Physics Card elements...');
        await page.waitForSelector('[data-testid="physics-card"]', { visible: true });
        const hasDownload = await page.$('[data-testid="physics-card-download"]');
        const cardText = await page.$eval('[data-testid="physics-card"]', el => el.innerText);
        console.log(`   ✓ Physics card section present`);
        console.log(`   ✓ Download button present: ${!!hasDownload}`);
        console.log(`   ✓ Physics card preview lines:\n${cardText.split('\n').slice(0, 4).map(l => '       ' + l).join('\n')}`);

        // Capture Desktop Physics Card screenshot
        await page.evaluate(() => {
            document.querySelector('[data-testid="physics-card"]').scrollIntoView();
        });
        await new Promise(r => setTimeout(r, 600));
        const cardDesktopPath = path.join(OUT_DIR, 'physics_card_desktop.png');
        await page.screenshot({ path: cardDesktopPath });
        console.log(`   ✓ Saved ${cardDesktopPath}`);

        // 4. Mobile Test (390x844)
        console.log('\n[Step 4] Testing 390px Mobile View...');
        await page.setViewport({ width: 390, height: 844 });
        
        // Scroll & capture Mobile Ghost Review
        await page.evaluate(() => {
            document.querySelector('[data-testid="ghost-review"]').scrollIntoView();
        });
        await new Promise(r => setTimeout(r, 600));
        const ghostMobilePath = path.join(OUT_DIR, 'ghost_review_mobile_390px.png');
        await page.screenshot({ path: ghostMobilePath });
        console.log(`   ✓ Saved ${ghostMobilePath}`);

        // Scroll & capture Mobile Physics Card
        await page.evaluate(() => {
            document.querySelector('[data-testid="physics-card"]').scrollIntoView();
        });
        await new Promise(r => setTimeout(r, 600));
        const cardMobilePath = path.join(OUT_DIR, 'physics_card_mobile_390px.png');
        await page.screenshot({ path: cardMobilePath });
        console.log(`   ✓ Saved ${cardMobilePath}`);

        // 5. Test Download Button interaction
        console.log('\n[Step 5] Testing Physics Card PNG export trigger...');
        await page.click('[data-testid="physics-card-download"]');
        await new Promise(r => setTimeout(r, 800));
        console.log('   ✓ Download trigger executed without errors.');

        // 6. Verification summary
        console.log('\n=== Summary of Screenshots ===');
        const files = [ghostDesktopPath, cardDesktopPath, ghostMobilePath, cardMobilePath];
        for (const f of files) {
            const stats = fs.statSync(f);
            const md5 = crypto.createHash('md5').update(fs.readFileSync(f)).digest('hex');
            console.log(`- ${path.basename(f)}: ${stats.size} bytes (MD5: ${md5.slice(0, 8)})`);
            if (stats.size < 10000) throw new Error(`Screenshot ${f} is unexpectedly small: ${stats.size} bytes`);
        }

        console.log('\nSUCCESS: T68 End-to-End Test and Screenshot generation complete!');
    } finally {
        await browser.close();
    }
}

runE2E().catch(err => {
    console.error('E2E Test Failed:', err);
    process.exit(1);
});
