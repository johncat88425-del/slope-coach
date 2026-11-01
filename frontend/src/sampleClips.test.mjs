import test from 'node:test';import assert from 'node:assert/strict';
import {createElement} from 'react';import {renderToStaticMarkup} from 'react-dom/server';
import {createApi,parseSampleClips} from '../.test-dist/api.js';import {SamplePicker} from '../.test-dist/SamplePicker.js';import {LanguageProvider} from '../.test-dist/i18n.js';
test('sample APIs use the v1.5 contract and pass the draft through unchanged without confirming conditions',async()=>{
 const catalog=[{name:'test/clip',kind:'synthetic',label:'Program-drawn clip'}],draft={draft_id:'sample',video_url:'/media/audits/sample/video.mp4',interview:{source:'mock',questions:[]},suggestion:null},calls=[];
 const api=createApi('https://backend.test',async(url,init)=>{calls.push([url,init.method??'GET',init.body]);return Response.json(calls.length===1?catalog:draft)});
 assert.deepEqual(await api.sampleClips(),catalog);assert.deepEqual(await api.sampleDraft(catalog[0].name),draft);
 assert.deepEqual(calls,[['https://backend.test/api/samples','GET',undefined],['https://backend.test/api/samples/test%2Fclip/draft','POST',undefined]]);
 assert.equal(draft.object_size_m,undefined);assert.equal(draft.camera_static,undefined);
});
test('sample lists validate provenance, and static mode blocks both endpoints before a request is made',async()=>{
 const valid=[{name:'one',kind:'generated',label:'Generated clip'},{name:'two',kind:'synthetic',label:'Program-drawn clip'}];
 assert.deepEqual(parseSampleClips(valid),valid);assert.deepEqual(parseSampleClips([]),[]);
 for(const invalid of [null,{},[{}],[{name:'x',kind:'recorded',label:'x'}],[{name:'x',kind:'generated',label:''}]])assert.throws(()=>parseSampleClips(invalid));
 let calls=0;const api=createApi('',async()=>{calls++;return Response.json([])},{demoOnly:true});
 await assert.rejects(api.sampleClips(),/Demo mode/);await assert.rejects(api.sampleDraft('one'),/Demo mode/);assert.equal(calls,0);
});
test('the sample picker makes no automatic request and exposes a bilingual keyboard button',()=>{
 let calls=0;const api=createApi('',async()=>{calls++;return Response.json([])});
 for(const lang of ['en','zh']){
  const html=renderToStaticMarkup(createElement(LanguageProvider,{value:lang},createElement(SamplePicker,{api,onDraft(){},onBusyChange(){}})));
  assert.match(html,/data-testid="try-sample"/);assert.match(html,/aria-expanded="false"/);assert.match(html,lang==='en'?/Try a sample clip/:/試用範例影片/);
  assert.doesNotMatch(html,/Preparing|<li|disabled/);
 }
 assert.equal(calls,0);
});

test('sample provenance stays inside the focused result card while backend values remain unchanged',async()=>{
 const {readFile}=await import('node:fs/promises'),{AuditResult}=await import('../.test-dist/AuditPage.js');
 const audit=JSON.parse(await readFile(new URL('../../data/demo/synthetic_toss_normal_g.json',import.meta.url),'utf8')),before=JSON.stringify(audit);
 const html=renderToStaticMarkup(createElement(AuditResult,{audit,replay:true,sampleKind:'synthetic'}));
 const label=html.indexOf('data-testid="sample-result-source"');assert.ok(label>html.indexOf('<article'));assert.ok(label<html.indexOf('</article>'));assert.ok(label<html.indexOf('data-testid="audit-details"'));
 assert.match(html,/Synthetic test clip/);assert.equal(JSON.stringify(audit),before);
});
