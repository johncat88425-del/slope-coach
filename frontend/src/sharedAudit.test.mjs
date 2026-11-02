import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {buildAuditShareLink,decodeSharedAudit,sharedPayloadFromHash,sharedUrlLimit,invalidSharedResult} from '../.test-dist/sharedAudit.js';
import {parseSavedAudit} from '../.test-dist/audit.js';
import {AuditResult} from '../.test-dist/AuditPage.js';
import {SharedAuditPage} from '../.test-dist/SharedAuditPage.js';
import {SiteFooter} from '../.test-dist/SiteHeader.js';
import {LanguageProvider,translateText} from '../.test-dist/i18n.js';

const saved=JSON.parse(await readFile(new URL('../../data/demo/real_own_2.json',import.meta.url)));
const origin='https://example.test';
const payload=link=>sharedPayloadFromHash(new URL(link.url).hash);
const render=(component,language='en')=>renderToStaticMarkup(h(LanguageProvider,{value:language},component));
async function pack(value){
 const zipped=new Uint8Array(await new Response(new Blob([JSON.stringify(value)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());
 return Buffer.from(zipped).toString('base64url');
}
async function unpack(text){return JSON.parse(await new Response(new Blob([Buffer.from(text,'base64url')]).stream().pipeThrough(new DecompressionStream('gzip'))).text())}

test('gzip links preserve all three outcomes, original numbers and multilingual model text without media or a server lookup',async()=>{
 for(const verdict of ['consistent','inconsistent','insufficient_data']){
  const audit={...saved,verdict,object_name:'球 🔬',explanation:{source:'model',text:'原文 — keep 0.123456789.'},reasons:['原始原因 0.123456789.'],video_url:'https://private.example/clip.mp4',overlay_url:'https://private.example/overlay.png',private_extra:'omit me'};
  const before=JSON.stringify(audit),link=await buildAuditShareLink(audit,origin);
  assert.equal(link.embedded,true);assert.ok(link.url.startsWith(origin+'/#r='));assert.ok(link.url.length<=sharedUrlLimit);
  assert.match(payload(link),/^[A-Za-z0-9_-]+$/);
  const decoded=await decodeSharedAudit(payload(link));
  assert.equal(decoded.audit.verdict,verdict);assert.deepEqual(decoded.audit.numbers,audit.numbers);
  assert.deepEqual(decoded.audit.reasons,audit.reasons);assert.deepEqual(decoded.audit.explanation,audit.explanation);
  assert.equal(decoded.audit.object_name,'球 🔬');assert.deepEqual(decoded.audit.events,audit.events);assert.deepEqual(decoded.audit.limits,audit.limits);
  assert.deepEqual(decoded.audit.points,audit.points);assert.equal(decoded.audit.video_url,'');assert.equal(decoded.audit.overlay_url,null);
  assert.equal(decoded.audit.private_extra,undefined);assert.equal(JSON.stringify(audit),before);
  const html=render(h(AuditResult,{audit:decoded.audit,replay:true}));assert.doesNotMatch(html,/<video|<img|private\.example/);
 }
});

test('vehicle assumptions, nullable explanation and all backend Muse outputs survive the same saved-result contract',async()=>{
 const vehicle=JSON.parse(await readFile(new URL('../../data/demo/synthetic_car_50kmh_braking.json',import.meta.url)));
 const audit={...vehicle,vehicle_class:'sedan',explanation:null,track_check:{same_object:true,note:'Original track note.',source:'model'},retake_tips:['Original tip.'],what_would_fit:{source:'model',text:'Original assumption.'}};
 assert.deepEqual(parseSavedAudit(JSON.stringify(audit)),audit);
 const {audit:decoded}=await decodeSharedAudit(payload(await buildAuditShareLink(audit,origin)));
 for(const key of ['vehicle_class','explanation','numbers','track_check','retake_tips','what_would_fit'])assert.deepEqual(decoded[key],audit[key]);
 assert.throws(()=>parseSavedAudit(JSON.stringify({...audit,vehicle_class:42})));
});

test('only original drawing tuples are selected for a long path; endpoints, measurements and original data remain unchanged',async()=>{
 const points=Array.from({length:1200},(_,i)=>[i/60,i+.123456789,i*i+.987654321]);
 const audit={...saved,points,ghost_points:points.map(([t,x,y])=>[t,x,y+1])},before=JSON.stringify(audit);
 const link=await buildAuditShareLink(audit,origin),decoded=await decodeSharedAudit(payload(link));
 assert.equal(link.pathReduced,true);assert.equal(decoded.pathReduced,true);
 for(const key of ['points','ghost_points']){
  const selected=decoded.audit[key];assert.equal(selected.length,600);assert.deepEqual(selected[0],audit[key][0]);assert.deepEqual(selected.at(-1),audit[key].at(-1));
  for(const point of selected)assert.ok(audit[key].some(original=>JSON.stringify(original)===JSON.stringify(point)));
 }
 assert.deepEqual(decoded.audit.numbers,audit.numbers);assert.equal(JSON.stringify(audit),before);
});

test('links honor the app base path and never retain an old audit path or query',async()=>{
 const link=await buildAuditShareLink(saved,origin,'/slope-coach/');
 assert.equal(new URL(link.url).pathname,'/slope-coach/');assert.equal(new URL(link.url).search,'');
 assert.equal(sharedPayloadFromHash('#r='),'');assert.equal(sharedPayloadFromHash('#r=abc'),'abc');
 for(const hash of ['#audit','#/audits/id','#home',''])assert.equal(sharedPayloadFromHash(hash),null);
});

test('oversized output falls back to the old ID link without truncating explanations or numbers',async()=>{
 let x=11;const noise=Array.from({length:65000},()=>{x=(Math.imul(x,1664525)+1013904223)>>>0;return String.fromCharCode(33+x%90)}).join('');
 const audit={...saved,reasons:[noise]},before=JSON.stringify(audit);
 const link=await buildAuditShareLink(audit,origin);
 assert.equal(link.embedded,false);assert.equal(link.url,origin+'/audit/'+encodeURIComponent(audit.audit_id));assert.equal(JSON.stringify(audit),before);
 assert.equal((await buildAuditShareLink(saved,origin,'/',10)).embedded,false);
});

test('missing or failed native compression uses an ID link, and missing decompression reports a local error',async()=>{
 const compression=globalThis.CompressionStream,decompression=globalThis.DecompressionStream;
 try{
  globalThis.CompressionStream=undefined;assert.equal((await buildAuditShareLink(saved,origin)).embedded,false);
  globalThis.CompressionStream=class{constructor(){throw new Error('unavailable')}};assert.equal((await buildAuditShareLink(saved,origin)).embedded,false);
  globalThis.DecompressionStream=undefined;await assert.rejects(decodeSharedAudit('anything'),/not supported in this browser/);
 }finally{globalThis.CompressionStream=compression;globalThis.DecompressionStream=decompression}
});

test('untrusted compressed input is bounded, schema-checked and cannot restore remote media',async()=>{
 const link=await buildAuditShareLink(saved,origin),value=await unpack(payload(link));
 const forged=await pack({...value,audit:{...value.audit,video_url:'https://remote.test/movie',overlay_url:'https://remote.test/image',private_extra:'no'}});
 const decoded=await decodeSharedAudit(forged);assert.equal(decoded.audit.video_url,'');assert.equal(decoded.audit.overlay_url,null);assert.equal(decoded.audit.private_extra,undefined);
 for(const text of ['', 'a','%invalid', 'a'.repeat(sharedUrlLimit+1),Buffer.from('not gzip').toString('base64url'),await pack({...value,v:99}),await pack({...value,audit:{...value.audit,numbers:{bad:'9'}}}),await pack({v:1,audit:{...saved,reasons:['x'.repeat(1024*1024+1)]},path_reduced:false})]){
  await assert.rejects(decodeSharedAudit(text),error=>error.message===invalidSharedResult);
 }
});

test('shared entry including invalid empty payload is local-only and does not mount upload, tour or spend requests',async()=>{
 const main=await readFile(new URL('./main.tsx',import.meta.url),'utf8');
 assert.match(main,/sharedPayload!==null \? <SharedAuditPage/);assert.match(main,/<SiteFooter[^>]*offline=\{sharedPayload!==null\}/);
 assert.match(main,/sharedPayload===null&&<AutoTour/);
 const page=render(h(SharedAuditPage,{payload:''}));assert.match(page,/Opening the saved result/);assert.doesNotMatch(page,/interview-file|audit-video-input/);
 const footer=render(h(SiteFooter,{api:{spend(){throw new Error('No request is allowed')}},route:'audit',offline:true}));assert.doesNotMatch(footer,/meta-spend/);
 const sharedSource=await readFile(new URL('./SharedAuditPage.tsx',import.meta.url),'utf8');assert.doesNotMatch(sharedSource,/createApi|getAudit|fetch\(/);
});

test('new share states and errors have Chinese translations; backend original strings stay unchanged',()=>{
 for(const text of ['Preparing share link…','This link contains the saved result and works after a server restart. Video is not included.','This result is too large or compressed links are unavailable. This server link expires after a restart; save the JSON.','Shared result','Shared saved result','The drawing path was simplified for sharing. The original JSON contains the full record.','Opening the saved result…',invalidSharedResult,'Compressed result links are not supported in this browser.']){
  assert.equal(translateText(text,'en'),text);assert.match(translateText(text,'zh'),/[\u3400-\u9fff]/);
 }
 assert.equal(translateText('Original backend reason 0.123456789.','zh'),'Original backend reason 0.123456789.');
});
