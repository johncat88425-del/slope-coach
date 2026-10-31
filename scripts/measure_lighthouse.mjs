import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const OUT_DIR = '/Users/aacc/Documents/slope-coach/data/lighthouse';
fs.mkdirSync(OUT_DIR, { recursive: true });

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
process.env.CHROME_PATH = CHROME_PATH;

const RUNS = [
  {
    id: 'online_mobile',
    title: 'Online GitHub Pages (Mobile)',
    url: 'https://johncat88425-del.github.io/slope-coach/',
    preset: null
  },
  {
    id: 'online_desktop',
    title: 'Online GitHub Pages (Desktop)',
    url: 'https://johncat88425-del.github.io/slope-coach/',
    preset: 'desktop'
  },
  {
    id: 'local_preview_mobile',
    title: 'Local Build Preview (Mobile)',
    url: 'http://127.0.0.1:4173/',
    preset: null
  },
  {
    id: 'local_preview_desktop',
    title: 'Local Build Preview (Desktop)',
    url: 'http://127.0.0.1:4173/',
    preset: 'desktop'
  }
];

const results = [];

for (const run of RUNS) {
  console.log(`\n====================================================`);
  console.log(`Running Lighthouse: ${run.title}`);
  console.log(`URL: ${run.url}`);
  console.log(`====================================================`);

  const jsonOut = path.join(OUT_DIR, `${run.id}.json`);
  const args = [
    '--yes',
    'lighthouse',
    run.url,
    '--output=json',
    `--output-path=${jsonOut}`,
    '--chrome-flags=--headless=new --no-sandbox',
    '--no-enable-error-reporting',
    '--only-categories=performance,accessibility,best-practices,seo'
  ];

  if (run.preset) {
    args.push(`--preset=${run.preset}`);
  }

  try {
    execFileSync('npx', args, {
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 90000
    });
    console.log(`Completed run for ${run.id}. Reading JSON output...`);

    const data = JSON.parse(fs.readFileSync(jsonOut, 'utf8'));
    const categories = data.categories || {};

    const scores = {
      performance: Math.round((categories.performance?.score ?? 0) * 100),
      accessibility: Math.round((categories.accessibility?.score ?? 0) * 100),
      bestPractices: Math.round((categories['best-practices']?.score ?? 0) * 100),
      seo: Math.round((categories.seo?.score ?? 0) * 100)
    };

    console.log(`Scores for ${run.title}:`, scores);

    // Identify audits scoring < 0.9 in categories scoring < 90
    const issues = [];
    for (const [catKey, catObj] of Object.entries(categories)) {
      const catScore = Math.round((catObj.score ?? 0) * 100);
      if (catScore < 90) {
        const auditRefs = catObj.auditRefs || [];
        const failingAudits = [];
        for (const ref of auditRefs) {
          const audit = data.audits[ref.id];
          if (audit && typeof audit.score === 'number' && audit.score < 0.9 && audit.scoreDisplayMode !== 'notApplicable' && audit.scoreDisplayMode !== 'informative') {
            failingAudits.push({
              id: ref.id,
              title: audit.title,
              score: Math.round(audit.score * 100),
              displayValue: audit.displayValue || '',
              description: audit.description || ''
            });
          }
        }
        issues.push({
          category: catObj.title,
          catScore,
          topFailingAudits: failingAudits.slice(0, 3)
        });
      }
    }

    results.push({
      ...run,
      scores,
      issues
    });
  } catch (err) {
    console.error(`Error running lighthouse for ${run.id}:`, err.message);
    if (err.stderr) console.error(err.stderr.toString());
    results.push({
      ...run,
      error: err.message
    });
  }
}

// Print Summary Table
console.log('\n\n====================================================');
console.log('=== LIGHTHOUSE SCORE SUMMARY ===');
console.log('====================================================');
console.log('| Target | Platform | Performance | Accessibility | Best Practices | SEO | Status |');
console.log('| :--- | :---: | :---: | :---: | :---: | :---: | :---: |');
for (const r of results) {
  if (r.scores) {
    const s = r.scores;
    const allPass = s.performance >= 90 && s.accessibility >= 90 && s.bestPractices >= 90 && s.seo >= 90;
    const platform = r.preset === 'desktop' ? 'Desktop' : 'Mobile';
    const target = r.id.startsWith('online') ? 'Online Pages' : 'Local Preview';
    console.log(`| ${target} | ${platform} | ${s.performance} | ${s.accessibility} | ${s.bestPractices} | ${s.seo} | ${allPass ? 'PASS (All ≥90)' : 'NEEDS ATTENTION'} |`);
  }
}

// Print Issues for any < 90
console.log('\n--- Details of Categories < 90 ---');
let foundBelow90 = false;
for (const r of results) {
  if (r.issues && r.issues.length > 0) {
    foundBelow90 = true;
    console.log(`\n[${r.title}]`);
    for (const issue of r.issues) {
      console.log(`  * ${issue.category} (${issue.catScore}/100):`);
      for (const a of issue.topFailingAudits) {
        console.log(`    - ${a.title} (${a.score}%): ${a.displayValue || a.description.slice(0, 80)}`);
      }
    }
  }
}
if (!foundBelow90) {
  console.log('None! All categories across all runs scored 90 or higher!');
}

fs.writeFileSync(path.join(OUT_DIR, 'summary.json'), JSON.stringify(results, null, 2));
console.log(`\nSaved summary to ${path.join(OUT_DIR, 'summary.json')}`);
