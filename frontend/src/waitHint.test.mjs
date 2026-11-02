import test from 'node:test';
import assert from 'node:assert/strict';
import {createElement as h} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {RequestStatus} from '../.test-dist/RequestStatus.js';
import {AuditProgress} from '../.test-dist/AuditProgress.js';
import {LanguageProvider} from '../.test-dist/i18n.js';
import {elapsedSeconds} from '../.test-dist/requestFeedback.js';
import {createApi,uploadAudit} from '../.test-dist/api.js';

test('both audit paths show bilingual elapsed seconds and the free-host wait hint before stage descriptions',()=>{
 for(const language of ['en','zh'])for(const node of [h(RequestStatus,{phase:'checking'}),h(AuditProgress,{percent:null}),h(AuditProgress,{percent:100})]){
  const html=render(h(LanguageProvider,{value:language},node));
  assert.match(html,/data-testid="request-elapsed" aria-live="off"/);
  assert.match(html,language==='en'?/Elapsed: 0 seconds/:/已經過： 0 秒/);
  assert.match(html,language==='en'?/On the free host, a check usually takes 1–4 minutes\. Please keep this page open\./:/免費主機上一次檢查約需 1–4 分鐘，請不要關閉頁面。/);
  assert.ok(html.indexOf('request-elapsed')<html.indexOf('analysis-waiting'));
  assert.ok(html.indexOf('audit-wait-hint')<html.indexOf('analysis-waiting'));
  assert.doesNotMatch(html,/aria-valuenow|<progress|\d+%/);
 }
 for(const phase of ['loading','preparing','scanning','uploading','transcribing'])assert.doesNotMatch(render(h(RequestStatus,{phase})),/audit-wait-hint/);
 assert.doesNotMatch(render(h(AuditProgress,{percent:25})),/audit-wait-hint/);
});

test('elapsed seconds continue through a long request without inventing a completion estimate',()=>{
 for(const seconds of [90,120,243,359,360,361])assert.equal(elapsedSeconds(1000,1000+seconds*1000),seconds);
});

test('fetch waits 360 seconds before aborting once, without an automatic resend',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});
 let signal,calls=0;
 const api=createApi('',async(_url,init)=>{calls++;signal=init.signal;return new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(Object.assign(new Error('aborted'),{name:'AbortError'})),{once:true}))});
 const request=api.auditFromDraft('fixture',{t_start:0,t_end:1,camera_static:true,assumed_model:'free_flight'});
 const expired=assert.rejects(request,/請求逾時/);
 t.mock.timers.tick(120000);assert.equal(signal.aborted,false);
 t.mock.timers.tick(239999);assert.equal(signal.aborted,false);
 t.mock.timers.tick(1);assert.equal(signal.aborted,true);
 await expired;assert.equal(calls,1);
});

test('a response after 243 seconds succeeds unchanged and clears the timeout',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});
 let finish,signal,calls=0;
 const api=createApi('',(_url,init)=>{calls++;signal=init.signal;return new Promise(resolve=>finish=resolve)});
 const request=api.getAudit('fixture'),result={audit_id:'fixture',numbers:{g_apparent_m_s2:0.123456}};
 t.mock.timers.tick(243000);assert.equal(signal.aborted,false);
 finish(Response.json(result));assert.deepEqual(await request,result);
 t.mock.timers.tick(360000);assert.equal(signal.aborted,false);assert.equal(calls,1);
});

test('XHR uses the same 360-second ceiling and preserves a returned result without resending',async()=>{
 let xhr,sends=0;
 const request=uploadAudit('/api/audits',new FormData(),()=>{},()=>xhr={upload:{},open(){},send(){sends++}});
 assert.equal(xhr.timeout,360000);
 const result={audit_id:'fixture',numbers:{g_apparent_m_s2:0.123456}};
 xhr.status=200;xhr.responseText=JSON.stringify(result);xhr.onload();
 assert.deepEqual(await request,result);assert.equal(sends,1);
});
