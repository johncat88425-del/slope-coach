import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';import {renderToStaticMarkup as render} from 'react-dom/server';
import {AuditResult} from '../.test-dist/AuditPage.js';import {TrackCheck,WhatWouldFit} from '../.test-dist/MuseAuditOutputs.js';import {RetakeGuide} from '../.test-dist/RetakeGuide.js';import {parseSavedAudit} from '../.test-dist/audit.js';import {LanguageProvider} from '../.test-dist/i18n.js';
const base=JSON.parse(await readFile(new URL('../../data/demo/generated_meta_clip4.json',import.meta.url),'utf8'));
const localized=(lang,node)=>render(h(LanguageProvider,{value:lang},node));
test('v1.3 saved outputs preserve all text, measurements and old records, rejecting malformed field shapes',()=>{
 const original=JSON.stringify(base);assert.deepEqual(parseSavedAudit(original),base);
 const a={...base,track_check:{source:'model',same_object:true,note:'The same object is followed.'},retake_tips:['Keep the object visible.'],what_would_fit:{source:'model',text:'Original conditional explanation.'}};
 assert.deepEqual(parseSavedAudit(JSON.stringify(a)),a);assert.deepEqual(parseSavedAudit(JSON.stringify({...base,track_check:null,retake_tips:null,what_would_fit:null})).numbers,base.numbers);
 for(const track_check of [{source:'mock',same_object:true,note:''},{source:'model',same_object:'false',note:''},{source:'model',same_object:false,note:4}])assert.throws(()=>parseSavedAudit(JSON.stringify({...base,track_check})));
 for(const retake_tips of [[],[''],['a','b','c','d'],'tip',[null]])assert.throws(()=>parseSavedAudit(JSON.stringify({...base,retake_tips})));
 for(const what_would_fit of [{source:'template',text:'x'},{source:'model',text:4},{source:'model',text:''}])assert.throws(()=>parseSavedAudit(JSON.stringify({...base,what_would_fit})));
 assert.equal(JSON.stringify(base),original);
});
test('track re-check distinguishes true, false and missing, with honest source and verbatim notes in both languages',()=>{
 for(const lang of ['en','zh'])for(const same_object of [true,false]){
  const html=localized(lang,h(TrackCheck,{check:{source:'model',same_object,note:'<span>Home</span>'}}));assert.match(html,/Muse Spark/);assert.match(html,/&lt;span&gt;Home&lt;\/span&gt;/);assert.doesNotMatch(html,/<span>Home<\/span>/);assert.match(html,same_object?(lang==='en'?/tracked the same object/:/追蹤的是同一個物體/):(lang==='en'?/may follow another object/:/可能追錯物體/));
 }
 for(const check of [null,undefined,{source:'mock',same_object:true,note:''}])assert.equal(render(h(TrackCheck,{check})),'');
});
test('Spark retake tips replace the fixed checklist only when supplied and keep original reasons',()=>{
 for(const lang of ['en','zh']){
  const model=localized(lang,h(RetakeGuide,{verdict:'insufficient_data',reasons:['Original reason'],modelTips:['Details','Keep the camera fixed.']}));assert.match(model,/data-testid="retake-source"/);assert.match(model,/Muse Spark/);assert.match(model,/>Details<\/li>/);assert.match(model,/Original reason/);assert.doesNotMatch(model,/Fixed checklist guidance|固定清單提示/);
  for(const modelTips of [null,undefined,[]]){const fallback=localized(lang,h(RetakeGuide,{verdict:'insufficient_data',reasons:['camera is not static'],modelTips}));assert.match(fallback,lang==='en'?/Fixed checklist guidance/:/固定清單提示/);assert.doesNotMatch(fallback,/data-testid="retake-source"/);}
 }
 assert.equal(render(h(RetakeGuide,{verdict:'consistent',reasons:[],modelTips:['tip']})),'');
});
test('conditional fit explanation is restricted to inconsistent free flight and never translated or recomputed',()=>{
 const a={...base,what_would_fit:{source:'model',text:'Details 0.123456789'}},before=JSON.stringify(a);
 for(const lang of ['en','zh']){const html=localized(lang,h(WhatWouldFit,{audit:a}));assert.match(html,/Details 0.123456789/);assert.match(html,/Muse Spark/);assert.match(html,lang==='en'?/What would fit this model/:/要怎樣才會一致/);}
 for(const audit of [{...a,verdict:'consistent'},{...a,verdict:'insufficient_data'},{...a,assumed_model:'vehicle'},{...a,what_would_fit:null}])assert.equal(render(h(WhatWouldFit,{audit})),'');
 assert.equal(JSON.stringify(a),before);
});
test('new guidance is outside collapsed evidence and does not change a backend refusal or fabricate fitted values',()=>{
 const a={...base,verdict:'insufficient_data',headline:null,explanation:undefined,numbers:{},track_check:{source:'model',same_object:false,note:''},retake_tips:['Keep one clear object visible.'],what_would_fit:null},before=JSON.stringify(a),html=render(h(AuditResult,{audit:a,replay:true}));
 assert.ok(html.indexOf('data-testid="track-check"')<html.indexOf('data-testid="audit-details"'));assert.ok(html.indexOf('data-testid="retake-guide"')<html.indexOf('data-testid="audit-details"'));assert.doesNotMatch(html,/data-testid="what-would-fit"|NaN|Infinity/);assert.equal(JSON.stringify(a),before);
});
