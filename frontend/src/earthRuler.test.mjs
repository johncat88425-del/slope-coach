import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {EarthAssumption} from '../.test-dist/EarthAssumption.js';
import {AuditResult} from '../.test-dist/AuditPage.js';
import {physicsCardLines,cardDisplayLine} from '../.test-dist/cardExport.js';
import {earthRulerReadings,earthRulerTitle,earthRulerNote,earthConditionPrefix} from '../.test-dist/earthRuler.js';
import {LanguageProvider,translateText} from '../.test-dist/i18n.js';

const read=async name=>JSON.parse(await readFile(new URL('../../data/demo/'+name+'.json',import.meta.url),'utf8'));

test('Earth readings use only supplied fields, preserving zero, negative angles and original precision',()=>{
 const numbers={if_earth_flight_time_s:0,if_earth_vertical_extent_m:28.7123456789,if_earth_launch_speed_m_s:3.123456789,if_earth_launch_angle_deg:-12.3456789},before=JSON.stringify(numbers);
 const rows=earthRulerReadings(numbers);assert.equal(rows.length,4);
 for(const r of rows)assert.equal(r.value,numbers[r.key]);
 const zh=render(h(LanguageProvider,{value:'zh'},h(EarthAssumption,{numbers})));
 assert.match(zh,/如果這是地球重力、正常速度/);assert.match(zh,/這是假設下的讀數，不是判定；慢動作會讓高度變大。/);
 assert.match(zh,/title="28.7123456789"/);assert.match(zh,/title="-12.3456789"/);assert.match(zh,/title="0"/);
 assert.equal(JSON.stringify(numbers),before);
 const partial=render(h(EarthAssumption,{numbers:{if_earth_flight_time_s:1.2345,if_earth_vertical_extent_m:NaN}}));
 assert.match(partial,/if_earth_flight_time_s/);assert.doesNotMatch(partial,/Vertical extent|Initial tracked|NaN/);
 assert.equal(render(h(EarthAssumption,{numbers:{g_apparent_m_s2:9.81}})),'');
});

test('saved results and evidence cards retain assumption context without changing the verdict or data',async()=>{
 const a=await read('generated_meta_clip4'),before=JSON.stringify(a);
 const html=render(h(AuditResult,{audit:a,replay:true})),lines=physicsCardLines(a);
 assert.ok(html.includes(earthRulerTitle));assert.ok(html.includes(earthRulerNote));
 assert.ok(html.indexOf('data-testid="earth-assumption"')<html.indexOf('data-testid="audit-details"'));
 assert.ok(lines.includes(earthRulerTitle));assert.ok(lines.includes(earthRulerNote));
 for(const r of earthRulerReadings(a.numbers))assert.ok(lines.includes(`${earthConditionPrefix} ${r.label}: ${r.text}`));
 assert.equal(a.verdict,'inconsistent');assert.equal(JSON.stringify(a),before);
 assert.equal(cardDisplayLine(a,earthRulerTitle,s=>translateText(s,'zh')),'如果這是地球重力、正常速度');
 assert.match(cardDisplayLine(a,'Vertical extent (m): 28.712',s=>translateText(s,'zh')),/垂直距離（m）： 28.712/);
 const unavailable=await read('generated_meta_clip2');
 assert.doesNotMatch(render(h(AuditResult,{audit:unavailable,replay:true})),/data-testid="earth-assumption"/);
 assert.ok(!physicsCardLines(unavailable).includes(earthRulerTitle));
});
