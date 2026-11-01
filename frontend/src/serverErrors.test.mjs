import test from 'node:test';
import assert from 'node:assert/strict';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {ApiError,createApi,friendlyApiError,isTemporaryApiError,serverBusyMessage,uploadAudit} from '../.test-dist/api.js';
import {ApiErrorNotice} from '../.test-dist/ApiErrorNotice.js';
import {LanguageProvider} from '../.test-dist/i18n.js';

const page='<!DOCTYPE html><html><head><title>Bad Gateway</title></head><body><script>privateDiagnostic()</script><h1>502</h1></body></html>';
test('gateway errors hide all server content and do not retry requests automatically',async()=>{
 for(const status of [502,503,504]){
  let calls=0;const api=createApi('',async()=>{calls++;return Response.json({detail:'private diagnostic'},{status})});
  await assert.rejects(api.sampleDraft('one'),e=>e instanceof ApiError&&e.status===status&&e.message===serverBusyMessage&&isTemporaryApiError(e));
  assert.equal(calls,1);assert.equal(friendlyApiError(new ApiError(status,'private diagnostic')),serverBusyMessage);
 }
});
test('HTML responses are suppressed for any status, including an HTML success page or JSON detail',async()=>{
 for(const [status,body,type] of [[500,page,'text/html'],[422,'<div>privateDiagnostic</div>','text/plain'],[200,page,'text/html'],[400,JSON.stringify({detail:page}),'application/json'],[200,'starting','text/html']]){
  const api=createApi('',async()=>new Response(body,{status,headers:{'Content-Type':type}}));
  await assert.rejects(api.sampleClips(),e=>e instanceof ApiError&&e.message===serverBusyMessage&&!e.message.includes('privateDiagnostic'));
 }
 for(const e of [new Error(page),new ApiError(500,page),page])assert.equal(friendlyApiError(e),serverBusyMessage);
});
test('rate and upload limit details and validation numbers are preserved verbatim',async()=>{
 for(const status of [429,413]){
  const detail='Limit reached: 50 MB / 10 requests. 請稍候。';
  const api=createApi('',async()=>Response.json({detail},{status}));
  await assert.rejects(api.sampleDraft('one'),e=>e.status===status&&friendlyApiError(e)===detail&&!isTemporaryApiError(e));
 }
 assert.match(friendlyApiError(new ApiError(422,'measurement 0.123456')),/measurement 0\.123456$/);
});
test('successful JSON retains backend text and numbers even if a text field contains markup',async()=>{
 const value={audit_id:'one',numbers:{g:0.123456},explanation:'literal <example> text'};
 const api=createApi('',async()=>Response.json(value));assert.deepEqual(await api.getAudit('one'),value);
 const csv='clip,label\nexample,<literal>\n';
 assert.equal(await createApi('',async()=>new Response(csv,{headers:{'Content-Type':'text/plain'}})).report('one','csv'),csv);
});
test('XHR gateway and HTML failures use the same safe message without an automatic resend',async()=>{
 for(const status of [200,502,503,504]){
  let x,sends=0;const promise=uploadAudit('/api/audits',new FormData(),()=>{},()=>x={upload:{},open(){},send(){sends++},getResponseHeader(){return 'text/html'}});
  x.status=status;x.responseText=page;x.onload();await assert.rejects(promise,e=>e.status===status&&e.message===serverBusyMessage);assert.equal(sends,1);
 }
});
test('temporary error UI is bilingual, focuses an alert and offers only an explicit retry',()=>{
 let retries=0;
 for(const lang of ['en','zh']){
  const html=renderToStaticMarkup(createElement(LanguageProvider,{value:lang},createElement(ApiErrorNotice,{error:new ApiError(502,page),onRetry(){retries++}})));
  assert.match(html,/role="alert"/);assert.match(html,/tabindex="-1"/);assert.match(html,/data-testid="api-retry"/);
  assert.match(html,lang==='en'?/server is starting or busy/:/伺服器正在啟動或忙碌中，請等 1 分鐘再試一次/);
  assert.match(html,lang==='en'?/Try again/:/重試/);assert.doesNotMatch(html,/privateDiagnostic|DOCTYPE|Bad Gateway/);
 }
 assert.equal(retries,0);
 const limited=renderToStaticMarkup(createElement(ApiErrorNotice,{error:new ApiError(429,'wait 10 minutes'),onRetry(){retries++}}));
 assert.match(limited,/wait 10 minutes/);assert.doesNotMatch(limited,/api-retry/);
 const disabled=renderToStaticMarkup(createElement(ApiErrorNotice,{error:new ApiError(503,'busy'),onRetry(){},disabled:true}));assert.match(disabled,/disabled/);
});
