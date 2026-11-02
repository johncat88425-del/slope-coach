import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {ApiError,createApi,friendlyApiError,requestTimeoutMessage,serverBusyMessage,uploadAudit} from '../.test-dist/api.js';
import {ApiErrorNotice} from '../.test-dist/ApiErrorNotice.js';
import {AuditResult} from '../.test-dist/AuditPage.js';
import {PhysicsCard} from '../.test-dist/PhysicsCard.js';
import {TrajectoryOverlay,Trajectory2D} from '../.test-dist/Trajectory.js';
import {LanguageProvider,translateText} from '../.test-dist/i18n.js';
import {formatNumber} from '../.test-dist/formatNumber.js';
import {earthConditionPrefix,earthRulerLines} from '../.test-dist/earthRuler.js';
import {cardDisplayLine,shareCardContent,downloadPhysicsCard} from '../.test-dist/cardExport.js';
import {auditMarkdown} from '../.test-dist/auditReport.js';
const audit=JSON.parse(await readFile(new URL('../../data/demo/synthetic_toss_normal_g.json',import.meta.url),'utf8'));
const localized=(language,node)=>render(h(LanguageProvider,{value:language},node));

test('empty gateway bodies and other empty API errors never leave a blank Reason suffix',async()=>{
 for(const message of ['', '  ', '\n']){
  assert.equal(friendlyApiError(new ApiError(502,message)),serverBusyMessage);
  const html=localized('en',h(ApiErrorNotice,{error:new ApiError(502,message),onRetry(){}}));
  assert.match(html,/server is starting or busy/);assert.match(html,/api-retry/);assert.doesNotMatch(html,/Reason:/);
 }
 for(const status of [400,404,422,500]){
  const message=friendlyApiError(new ApiError(status,' '));assert.ok(message.trim());assert.doesNotMatch(message,/Reason:\s*$/);
 }
 const api=createApi('',async()=>new Response('',{status:502}));
 await assert.rejects(api.sampleClips(),e=>e.message===serverBusyMessage);
});

test('fetch and XHR timeouts recommend a shorter window, with both interface languages and no record-loading instruction',async()=>{
 const api=createApi('',async()=>{throw Object.assign(new Error('aborted'),{name:'AbortError'})});
 await assert.rejects(api.getAudit('fixture'),e=>e.message===requestTimeoutMessage);
 let xhr,sends=0;
 const pending=uploadAudit('/api/audits',new FormData(),()=>{},()=>xhr={upload:{},open(){},send(){sends++}});
 xhr.ontimeout();await assert.rejects(pending,e=>e.message===requestTimeoutMessage);assert.equal(sends,1);
 for(const language of ['en','zh']){
  const html=localized(language,h(ApiErrorNotice,{error:new Error(requestTimeoutMessage)}));
  assert.match(html,language==='en'?/shorter time window \(0.5–2 seconds\)/:/更短的時間窗（0.5–2 秒）/);
  assert.doesNotMatch(html,/load.*record|重新讀取|api-retry/);
  if(language==='en')assert.doesNotMatch(html,/[\u3400-\u9fff]/);
 }
});

test('result metadata and tracking accessible labels follow the selected language',()=>{
 for(const language of ['en','zh']){
  const html=localized(language,h(AuditResult,{audit,replay:false}));
  const metadata=html.match(/<p data-testid="audit-metadata">(.*?)<\/p>/s)[1];
  assert.match(metadata,language==='en'?/Model:.*Window:/:/運動模型：.*時間窗：/);
  if(language==='en')assert.doesNotMatch(metadata,/[\u3400-\u9fff]/);
  const overlay=localized(language,h(TrajectoryOverlay,{url:'/media/fixture.png'}));
  assert.match(overlay,language==='en'?/alt="Backend tracking path over the original video frame"/:/alt="後端追蹤軌跡疊加於原始影片影格"/);
  const trajectory=localized(language,h(Trajectory2D,{points:[{t:0,x:1,y:2}]}));
  assert.match(trajectory,language==='en'?/aria-label="Observed trajectory in orange/:/aria-label="橘色實測軌跡/);
 }
});

test('very small Earth ratios are described rather than rounded to zero, without changing backend numbers',()=>{
 for(const value of [0,.0001,.004,.009999]){
  const record={...audit,numbers:{g_vs_earth:value}},before=JSON.stringify(record);
  assert.equal(formatNumber(value,'g_vs_earth'),'less than 1/100 of Earth');
  assert.equal(shareCardContent(record).value,'less than 1/100');
  assert.match(localized('zh',h(PhysicsCard,{audit:record})),/不到百分之一/);
  assert.equal(JSON.stringify(record),before);
 }
 assert.equal(formatNumber(.01,'g_vs_earth'),'0.01');
 assert.equal(shareCardContent({...audit,numbers:{g_vs_earth:.01}}).value,'0.0100×');
 assert.equal(formatNumber(.004),'0.004');
});

test('every Earth-only field stays conditional in UI, print, evidence lines and Markdown, while original values remain intact',()=>{
 const record={...audit,numbers:{if_earth_vertical_extent_m:67.512345,if_earth_custom_reading:3.456789}},before=JSON.stringify(record);
 const html=localized('en',h(AuditResult,{audit:record,replay:true}));
 for(const key of Object.keys(record.numbers))assert.ok(html.includes(`<span>${earthConditionPrefix}</span> ${key}`));
 assert.match(html,/title="67.512345"/);
 for(const line of earthRulerLines(record.numbers).filter(line=>line.includes('Vertical extent'))){
  assert.ok(line.startsWith(earthConditionPrefix));assert.match(cardDisplayLine(record,line,s=>translateText(s,'zh')),/如果這是地球重力： 垂直距離/);
 }
 const md=auditMarkdown(record);for(const key of Object.keys(record.numbers))assert.ok(md.includes(`${earthConditionPrefix} ${key}`));
 assert.ok(md.includes('67.512345'));assert.equal(JSON.stringify(record),before);
});

test('non-consistent share cards keep the first backend reason verbatim; consistent and missing reasons add none',()=>{
 for(const verdict of ['inconsistent','insufficient_data']){
  const record={...audit,verdict,reasons:['Original reason 0.123456.','Second reason.']},before=JSON.stringify(audit);
  assert.equal(shareCardContent(record).reason,record.reasons[0]);
  for(const language of ['en','zh'])assert.ok(localized(language,h(PhysicsCard,{audit:record})).includes('Original reason 0.123456.'));
  assert.equal(JSON.stringify(audit),before);
 }
 assert.equal(shareCardContent({...audit,verdict:'consistent',reasons:['not a failure']}).reason,null);
 assert.equal(shareCardContent({...audit,verdict:'inconsistent',reasons:[]}).reason,null);
});

test('the PNG actually draws the first reason above the footer, retaining its numbers',async()=>{
 const previous=globalThis.document,create=URL.createObjectURL,revoke=URL.revokeObjectURL;
 const drawn=[],ctx={measureText:s=>({width:s.length*12}),fillRect(){},fillText:(text,x,y)=>drawn.push({text,y})};
 globalThis.document={createElement:tag=>tag==='canvas'?{getContext:()=>ctx,toBlob(cb,type){cb(new Blob(['fixture'],{type}))}}:{click(){}}};
 URL.createObjectURL=()=> 'blob:fixture';URL.revokeObjectURL=()=>{};
 try{
  for(const verdict of ['inconsistent','insufficient_data']){
   await downloadPhysicsCard({...audit,verdict,reasons:['Original reason 0.123456.','Second reason.']});
   const reason=drawn.find(row=>row.text==='Original reason 0.123456.');assert.ok(reason);assert.ok(reason.y<1660);
   assert.ok(!drawn.some(row=>row.text==='Second reason.'));
  }
 }finally{globalThis.document=previous;URL.createObjectURL=create;URL.revokeObjectURL=revoke}
});

test('the copy-link action includes the restart warning and a JSON save alternative in both languages',()=>{
 for(const language of ['en','zh']){
  const html=localized(language,h(AuditResult,{audit,replay:false}));
  assert.ok(html.indexOf('share-link-note')>html.indexOf('copy-audit-link'));
  assert.match(html,language==='en'?/Links on the free server stop working after a restart\. Save the JSON\./:/免費伺服器重啟後連結會失效，請存 JSON。/);
  assert.match(html,/data-testid="audit-export-json"/);
 }
});
