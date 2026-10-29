import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {FinalDemo} from '../.test-dist/FinalDemo.js';
import {parseSavedAudit} from '../.test-dist/audit.js';
import {comparisonKeys,openingExampleKeys,savedOutcomeCaption} from '../.test-dist/demoSelection.js';
import {LanguageProvider,translateText} from '../.test-dist/i18n.js';

const dir=new URL('../../data/demo/',import.meta.url);
async function entries(){const names=(await readdir(dir)).filter(n=>/^(real_own_|generated_).*\.json$/.test(n)).sort();return Promise.all(names.map(async name=>({key:name.replace('.json',''),audit:parseSavedAudit(await readFile(new URL(name,dir),'utf8'))})));}
const escape=text=>text.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;');

test('final comparison replays all ten SAM records without altering or substituting their content',async()=>{
 const records=await entries(),before=JSON.stringify(records);
 const html=renderToStaticMarkup(createElement(FinalDemo,{records,synthetic:[]}));
 assert.equal(records.length,10);assert.equal((html.match(/data-demo-key=/g)||[]).length,10);
 assert.deepEqual(records.reduce((totals,{audit})=>({...totals,[audit.verdict]:(totals[audit.verdict]??0)+1}),{}),{inconsistent:4,insufficient_data:3,consistent:3});
 for(const {key,audit} of records){
  assert.equal(audit.track_source,'sam',key);assert.equal(audit.explanation.source,'model',key);
  assert.ok(html.includes('data-demo-key="'+key+'"'),key);
  assert.ok(html.includes(escape(audit.explanation.text)),key);
  if(audit.headline)assert.ok(html.includes(escape(audit.headline.text)),key);
  for(const reason of audit.reasons)assert.ok(html.includes(escape(reason)),key);
 }
 assert.equal(JSON.stringify(records),before);
 assert.doesNotMatch(html,/<video|src="\/media|including the inconsistent result|cause unknown|Performance on recorded experiments remains unverified/);
 assert.doesNotMatch(html,/<details[^>]*\bopen/);
});

test('final example entry points cover all outcomes and use a consistent/inconsistent comparison',async()=>{
 const records=await entries();const find=key=>records.find(r=>r.key===key).audit;
 assert.deepEqual(openingExampleKeys.map(key=>find(key).verdict),['consistent','inconsistent','insufficient_data']);
 assert.deepEqual(comparisonKeys.map(key=>find(key).verdict),['consistent','inconsistent']);
 for(const key of openingExampleKeys){const audit=find(key),caption=savedOutcomeCaption(audit);assert.notEqual(translateText(caption,'zh'),caption);assert.doesNotMatch(caption,/reliable tracked positions/);}
 assert.match(savedOutcomeCaption({verdict:'insufficient_data'}),/recorded reasons/);
});

test('Chinese interface preserves final English model content and keeps development fixtures separate',async()=>{
 const records=await entries();const synthetic=[parseSavedAudit(await readFile(new URL('synthetic_toss_normal_g.json',dir),'utf8'))];
 const html=renderToStaticMarkup(createElement(LanguageProvider,{value:'zh'},createElement(FinalDemo,{records,synthetic})));
 assert.match(html,/程式繪製的測試範例/);assert.match(html,/每筆儲存結果保留原始量測/);
 assert.ok(html.indexOf('data-testid="synthetic-demo"')>html.indexOf('data-testid="generated-demo"'));
 for(const {audit} of records)assert.ok(html.includes(escape(audit.explanation.text)));
 const code=await readFile(new URL('./DemoPage.tsx',import.meta.url),'utf8');
 assert.match(code,/records=\{demoRecords\}/);assert.doesNotMatch(code,/real_own_\d\.json/);
});
