import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';import {renderToStaticMarkup as render} from 'react-dom/server';
import {AuditResult} from '../.test-dist/AuditPage.js';import {PhysicsCard} from '../.test-dist/PhysicsCard.js';import {CarPreview} from '../.test-dist/CarPreview.js';import {LanguageProvider} from '../.test-dist/i18n.js';
const keys=['synthetic_car_50kmh_braking','synthetic_car_3g_launch'];const records=await Promise.all(keys.map(async key=>({key,audit:JSON.parse(await readFile(new URL('../../data/demo/'+key+'.json',import.meta.url),'utf8'))})));
test('the single outlined result download is after the result card and outside all collapsed details',()=>{
 const before=JSON.stringify(records[0].audit);
 for(const language of ['en','zh']){
  const html=render(h(LanguageProvider,{value:language},h(AuditResult,{audit:records[0].audit,replay:true})));
  const download=html.indexOf('data-testid="physics-card-download"');assert.ok(download>html.lastIndexOf('</article>'));assert.ok(download>html.lastIndexOf('</details>'));assert.equal((html.match(/data-testid="physics-card-download"/g)||[]).length,1);
  const button=html.match(/<button[^>]*data-testid="physics-card-download"[^>]*>/)[0];assert.match(button,/class="share-download"/);assert.doesNotMatch(button,/primary|disabled/);assert.match(html,language==='en'?/Download share card PNG/:/下載分享卡 PNG/);
  assert.doesNotMatch(html.match(/<details data-testid="audit-details"[^>]*>/)[0],/open/);
 }
 assert.equal(JSON.stringify(records[0].audit),before);
 assert.equal((render(h(PhysicsCard,{audit:records[0].audit})).match(/data-testid="physics-card-download"/g)||[]).length,1);
});
test('Cars preview keeps synthetic provenance and reads both metrics from the saved backend records',()=>{
 const before=JSON.stringify(records),html=render(h(CarPreview,{records}));assert.match(html,/data-category="cars"/);assert.match(html,/Synthetic test clips/);assert.match(html,/>Cars<\/button>/);assert.equal((html.match(/data-testid="car-case"/g)||[]).length,2);
 for(const {key,audit} of records){assert.ok(html.includes(audit.numbers.speed_km_h.toFixed(0)+' km/h'));assert.ok(html.includes(audit.numbers.accel_g.toFixed(2)+' g'));assert.ok(html.includes('href="#examples/'+key+'"'));}
 assert.doesNotMatch(html,/Generated test clip|Recorded by john|Tracked by SAM/);assert.equal(JSON.stringify(records),before);
 const zh=render(h(LanguageProvider,{value:'zh'},h(CarPreview,{records})));assert.match(zh,/程式模擬測試片/);assert.match(zh,/查看煞車範例/);assert.match(zh,/查看加速範例/);
});
test('missing vehicle metrics stay empty instead of becoming a fabricated speed or acceleration',()=>{
 const html=render(h(CarPreview,{records:records.map(row=>({...row,audit:{...row.audit,numbers:{}}}))}));assert.match(html,/Measurement unavailable/);assert.doesNotMatch(html,/km\/h|NaN|undefined|Infinity/);
});
