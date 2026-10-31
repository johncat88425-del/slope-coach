import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {AuditResult,AuditPage} from '../.test-dist/AuditPage.js';
import {AuditDimensionField} from '../.test-dist/VehicleModel.js';
import {parseSavedAudit,validateAuditInput,verdictText} from '../.test-dist/audit.js';
import {parseVoiceAnswer,voiceFieldPatch} from '../.test-dist/voiceAnswer.js';
import {LanguageProvider} from '../.test-dist/i18n.js';
import {createApi} from '../.test-dist/api.js';

const sample=async name=>parseSavedAudit(await readFile(new URL('../../data/demo/synthetic_car_'+name+'.json',import.meta.url),'utf8'));
const zh=node=>render(h(LanguageProvider,{value:'zh'},node));

test('vehicle saved records, verdicts and confirmed voice fields use the vehicle model',async()=>{
 assert.equal(verdictText('consistent','vehicle'),'與車子行駛模型一致');
 assert.equal(verdictText('inconsistent','vehicle'),'與車子行駛模型不一致');
 assert.equal(verdictText('insufficient_data','vehicle'),'與車子行駛模型無法判斷');
 const a=await sample('50kmh_braking');assert.equal(a.assumed_model,'vehicle');
 assert.deepEqual(parseSavedAudit(JSON.stringify(a)),a);
 assert.deepEqual(validateAuditInput('0','2',''),[]);
 assert.deepEqual(validateAuditInput('0','2','4.5'),[]);
 for(const size of ['0','-1','NaN','Infinity'])assert.ok(validateAuditInput('0','2',size).length);
 assert.throws(()=>parseSavedAudit(JSON.stringify({...a,assumed_model:'truck'})));
 assert.throws(()=>parseSavedAudit(JSON.stringify({...a,object_size_m:0})));
 const voice={source:{transcript:'muse-voice-transcribe-1.0',fields:'muse-spark-1.3'},transcript:'A car about four and a half metres long.',fields:{assumed_model:{value:'vehicle',confirmed:false},object_size_m:{value:4.5,confirmed:false}}};
 assert.deepEqual(parseVoiceAnswer(voice),voice);
 assert.deepEqual(voiceFieldPatch('assumed_model','vehicle'),{model:'vehicle'});
 assert.deepEqual(voiceFieldPatch('object_size_m',4.5),{size:'4.5'});
 assert.throws(()=>parseVoiceAnswer({...voice,fields:{assumed_model:{value:'vehicle',confirmed:true}}}));
});

test('both upload paths offer vehicle; dimension guidance is bilingual and never fills a guessed length',()=>{
 const form=zh(h(AuditPage,{api:createApi()}));assert.match(form,/<option value="vehicle">車子從側面開過（鏡頭固定）/);
 for(const lang of ['zh','en']){
  const html=render(h(LanguageProvider,{value:lang},h(AuditDimensionField,{model:'vehicle',value:'',onChange(){throw Error('render must not fill a value')}})));
  assert.match(html,/value=""/);assert.match(html,/4\.5/);assert.match(html,/4\.8/);assert.match(html,/3\.5/);assert.match(html,/aria-describedby="[^"]+"/);
  assert.match(html,lang==='zh'?/車身長度（公尺）/:/Car body length \(metres\)/);
  assert.match(html,lang==='zh'?/兩個答案一樣才判/:/only when they agree/);
  assert.match(html,lang==='zh'?/整台都在畫面裡、從左開到右/:/whole car is visible and drives from left to right/);
 }
});

test('vehicle summaries use backend km/h and signed acceleration without recomputing or mutating evidence',async()=>{
 const a=await sample('50kmh_braking'),before=JSON.stringify(a);
 // Deliberately unrelated values ensure the UI never derives speed from m/s or length.
 const numbers={...a.numbers,speed_km_h:71.6,speed_m_s:999,accel_g:0.654321,accel_m_s2:-99};
 const html=zh(h(AuditResult,{audit:{...a,numbers},replay:true}));
 assert.doesNotMatch(html,/9\.81 m\/s|No gravity estimate/);
 assert.match(html,/72 km\/h/);assert.match(html,/0\.65 g/);assert.match(html,/煞車/);
 assert.match(html,/每秒走幾個車身長/);assert.match(html,/這台車要有/);assert.match(html,/才剛好是 1\.2 g/);
 assert.match(html,/程式模擬/);assert.ok(html.indexOf('程式模擬')<html.indexOf('data-testid="audit-details"'));
 assert.match(html,/title="71\.6"/);assert.equal(numbers.accel_g,0.654321);assert.equal(JSON.stringify(a),before);
 const launch=await sample('3g_launch');assert.equal(launch.verdict,'inconsistent');
 assert.match(zh(h(AuditResult,{audit:launch,replay:true})),/加速/);
 const zero=zh(h(AuditResult,{audit:{...a,numbers:{speed_km_h:0,accel_g:0,accel_m_s2:0,speed_car_lengths_s:0,car_length_for_max_accel_m:0}},replay:true}));
 assert.match(zero,/0 km\/h/);assert.match(zero,/0\.00 g/);
});

test('unknown length and missing backend fields never produce SI speed or invented vehicle rows',async()=>{
 const a=await sample('50kmh_braking');
 for(const object_size_m of [null,undefined]){
  const html=render(h(AuditResult,{audit:{...a,object_size_m,explanation:undefined},replay:true}));
  assert.doesNotMatch(html,/km\/h|data-testid="vehicle-speed"|data-testid="vehicle-acceleration"/);
  assert.match(html,/data-testid="vehicle-length-speed"/);
 }
 const empty=render(h(AuditResult,{audit:{...a,numbers:{}},replay:true}));
 assert.doesNotMatch(empty,/data-testid="vehicle-(?:speed|acceleration|length-speed|required-length)"|NaN|Infinity|undefined/);
 assert.doesNotMatch(render(h(AuditResult,{audit:{...a,assumed_model:'free_flight'},replay:true})),/data-testid="vehicle-measurements"/);
});

test('vehicle API requests preserve confirmed length and omit unknown length',async()=>{
 const calls=[];const api=createApi('',async(url,init)=>{calls.push(init.body);return Response.json(await sample('50kmh_braking'))});
 await api.auditFromDraft('car-draft',{t_start:1,t_end:3,camera_static:true,assumed_model:'vehicle',object_size_m:4.512345});
 await api.audit(new File(['fixture'],'car.mp4'),1,3,true,undefined,'vehicle');
 assert.equal(calls[0].get('assumed_model'),'vehicle');assert.equal(calls[0].get('object_size_m'),'4.512345');
 assert.equal(calls[1].get('assumed_model'),'vehicle');assert.equal(calls[1].has('object_size_m'),false);
});

// Vehicle results still expose the original video when it is available.
test('vehicle replay retains video review without introducing a gravity ghost model',async()=>{
 const a=await sample('50kmh_braking');
 const html=render(h(AuditResult,{audit:{...a,video_url:'/media/car.mp4'}}));
 assert.match(html,/data-testid="ghost-video"/);assert.match(html,/src="\/media\/car.mp4"/);
 assert.match(html,/Tracked motion replay/);assert.doesNotMatch(html,/expected positions under 9\.81/);
});
