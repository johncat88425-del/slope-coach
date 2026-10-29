import fs from 'node:fs';
import crypto from 'node:crypto';
import puppeteer from '../frontend/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT_DIR = './docs/screens';

async function main() {
    fs.mkdirSync(OUT_DIR, { recursive: true });

    const browser = await puppeteer.launch({
        executablePath: CHROME_PATH,
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });

    // 1. Results Wall (route #wall)
    console.log('1. Navigating to http://127.0.0.1:5173/#wall...');
    await page.goto('http://127.0.0.1:5173/#wall', { waitUntil: 'networkidle0' });
    await page.waitForSelector('[data-testid="results-wall"]');
    await page.evaluate(() => {
        document.querySelector('[data-testid="results-wall"]').scrollIntoView();
    });
    await new Promise(r => setTimeout(r, 600));
    const wallPath = `${OUT_DIR}/results_wall_mobile_390px.png`;
    await page.screenshot({ path: wallPath });
    console.log('Saved', wallPath);

    // 2. Pair Comparison (route #compare)
    console.log('2. Navigating to http://127.0.0.1:5173/#compare...');
    await page.goto('http://127.0.0.1:5173/#compare', { waitUntil: 'networkidle0' });
    await page.waitForSelector('[data-testid="pair-comparison"]');
    await page.evaluate(() => {
        document.querySelector('[data-testid="pair-comparison"]').scrollIntoView();
    });
    await new Promise(r => setTimeout(r, 600));
    const comparePath = `${OUT_DIR}/pair_comparison_mobile_390px.png`;
    await page.screenshot({ path: comparePath });
    console.log('Saved', comparePath);

    // 3. Ghost Review (route #demo)
    console.log('3. Navigating to http://127.0.0.1:5173/#demo...');
    await page.goto('http://127.0.0.1:5173/#demo', { waitUntil: 'networkidle0' });
    await page.waitForSelector('[data-testid="ghost-review"]');
    await page.evaluate(() => {
        const el = document.querySelector('[data-testid="ghost-review"]');
        if (el) {
            const details = el.closest('details');
            if (details) details.open = true;
            el.scrollIntoView();
        }
    });
    await new Promise(r => setTimeout(r, 600));
    const ghostPath = `${OUT_DIR}/ghost_review_mobile_390px.png`;
    await page.screenshot({ path: ghostPath });
    console.log('Saved', ghostPath);

    await browser.close();

    // Check MD5 hashes
    const files = [wallPath, comparePath, ghostPath];
    const hashes = files.map(f => {
        const data = fs.readFileSync(f);
        return crypto.createHash('md5').update(data).digest('hex');
    });

    console.log('\n=== MD5 Check ===');
    files.forEach((f, i) => console.log(`${f}: ${hashes[i]}`));
    const uniqueHashes = new Set(hashes);
    if (uniqueHashes.size === 3) {
        console.log('SUCCESS: All 3 mobile screenshots have DISTINCT MD5 hashes!\n');
    } else {
        throw new Error(`FAILURE: Duplicate hashes detected! (${uniqueHashes.size} unique out of 3)`);
    }
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
