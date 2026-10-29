import {LanguageProvider} from '../.test-dist/i18n.js';
import test from 'node:test';import assert from 'node:assert/strict';import {createElement} from 'react';import {renderToStaticMarkup as rawRender} from 'react-dom/server';
import {AuditPage,AuditResult,EventTimeline} from '../.test-dist/AuditPage.js';import {createApi} from '../.test-dist/api.js';import {parseSavedAudit,validateAuditInput} from '../.test-dist/audit.js';
const fixture=verdict=>({audit_id:'ui-fixture',created_at:'2026-10-27',assumed_model:'free_flight',t_start:0,t_end:1,camera_static:true,object_size_m:null,video_url:'/media/test/clip.mp4',overlay_url:null,track_source:'frame_diff',verdict,reasons:['fixture reason'],numbers:{sentinel:123.456789},points:[],events:[],limits:['fixture limitation']});
test('all three verdicts render as model-relative outcomes with evidence and limits',()=>{
 const labels={consistent:'與地球上的自由飛行一致',inconsistent:'與地球上的自由飛行不一致',insufficient_data:'無法判斷這段影片'};
 for(const v of Object.keys(labels)){const html=render(createElement(AuditResult,{audit:fixture(v)}));assert.ok(html.includes(labels[v]));for(const s of ['fixture reason','fixture limitation','123.456789'])assert.ok(html.includes(s));assert.ok(!html.includes('role="alert"'))}
});
test('audit form and each outcome avoid provenance claims and render unknown numbers as absent',()=>{
 const form=render(createElement(AuditPage,{api:createApi('',async()=>Response.json({}))}));
 for(const html of [form,...['consistent','inconsistent','insufficient_data'].map(v=>render(createElement(AuditResult,{audit:{...fixture(v),numbers:{}}})) )])assert.doesNotMatch(html,/真影片|假影片|AI 生成|AI影片|第一個|偵測真假/);
 assert.match(render(createElement(AuditResult,{audit:{...fixture('insufficient_data'),numbers:{}}})),/尚無可提供的數值/);
});
test('audit upload sends explicit window/model/camera and does not invent size',async()=>{
 let body,path;const api=createApi('',async(url,init)=>{path=url;body=init.body;return Response.json(fixture('insufficient_data'))});
 await api.audit(new File(['fixture'],'test.mp4'),0,2,false);
 assert.equal(path,'/api/audits');assert.equal(body.get('assumed_model'),'free_flight');assert.equal(body.get('camera_static'),'false');assert.equal(body.get('t_start'),'0');assert.equal(body.get('t_end'),'2');assert.equal(body.has('object_size_m'),false);
});
test('window and optional dimension validation rejects missing or non-finite inputs',()=>{assert.deepEqual(validateAuditInput('0','2',''),[]);for(const args of [['','2',''],['1','1',''],['-1','2',''],['0','Infinity',''],['0','2','0'],['0','2','NaN']])assert.ok(validateAuditInput(...args).length)});

function render(node){return rawRender(createElement(LanguageProvider,{value:'zh'},node))}

test('saved audit validation preserves numbers and rejects malformed or unsupported results',()=>{
 const a=fixture('consistent'); assert.deepEqual(parseSavedAudit(JSON.stringify(a)),a);
 for(const bad of [{...a,assumed_model:'unknown'},{...a,verdict:'authentic'},{...a,numbers:{x:'9'}},{...a,points:[[0,1]]},{...a,events:[{kind:'x',t_s:null,detail:'x'}]}])assert.throws(()=>parseSavedAudit(JSON.stringify(bad)));
 assert.throws(()=>parseSavedAudit('not json'));
});
test('offline replay explicitly labels saved output and never requests remote media',()=>{
 const html=render(createElement(AuditResult,{audit:{...fixture('consistent'),overlay_url:'/media/test/overlay.svg'},replay:true}));
 assert.match(html,/已儲存結果重播/);assert.doesNotMatch(html,/<img|<video/);assert.match(html,/123.456789/);
});

test('bounce upload, saved replay and verdicts use the selected model with raw rebound ratios',async()=>{
 let body;const api=createApi('',async(url,init)=>{body=init.body;return Response.json({...fixture('consistent'),assumed_model:'bounce'})});
 await api.audit(new File(['fixture'],'bounce.mp4'),0,2,true,undefined,'bounce');assert.equal(body.get('assumed_model'),'bounce');
 for(const v of ['consistent','inconsistent','insufficient_data']){const a={...fixture(v),assumed_model:'bounce',numbers:{rebound_ratio_1:0.7654321}};assert.deepEqual(parseSavedAudit(JSON.stringify(a)),a);const html=render(createElement(AuditResult,{audit:a,replay:true}));assert.match(html,v==='insufficient_data'?/無法判斷這段影片/:/被動彈跳/);assert.match(html,/rebound_ratio_1/);assert.match(html,/0.7654321/);assert.doesNotMatch(html,/自由落體模型/)}
});

test('event timeline sorts exact timestamps, keeps backend details and labels all event types',()=>{
 const events=[{kind:'position_jump',t_s:2,detail:'raw position detail'},{kind:'vanished',t_s:0.123456,detail:'raw missing detail'},{kind:'size_jump',t_s:1,detail:'raw size detail'}];
 const html=rawRender(createElement(EventTimeline,{events}));assert.ok(html.indexOf('0.123456')<html.indexOf('2 s'));for(const label of ['Disappearance','Size jump','Position jump','raw missing detail'])assert.ok(html.includes(label));assert.equal(events[0].t_s,2);
});
test('size-trend refusal shows the exact backend value and retains backend reasons',()=>{
 const html=rawRender(createElement(AuditResult,{audit:{...fixture('insufficient_data'),numbers:{size_trend:-0.456789}}}));assert.match(html,/Size trend limitation/);assert.match(html,/-0.456789/);assert.match(html,/fixture reason/);assert.match(html,/does not establish a cause/);
});

test('audit links round-trip encoded IDs, resolve audit route and use read-only GET',async()=>{
 const {auditHash,auditIdFromHash,resolveRoute}=await import('../.test-dist/experiment.js');
 for(const id of ['audit-123','id with space','id/slash']){assert.equal(auditIdFromHash(auditHash(id)),id);assert.equal(resolveRoute(auditHash(id)),'audit')}
 for(const hash of ['#/audits/','#/audits/%ZZ','#setup'])assert.equal(auditIdFromHash(hash),null);
 let path,init;await createApi('',async(p,i)=>{path=p;init=i;return Response.json(fixture('consistent'))}).getAudit('id/slash');assert.equal(path,'/api/audits/id%2Fslash');assert.equal(init.method,undefined);
 const html=rawRender(createElement(AuditResult,{audit:fixture('consistent')}));assert.match(html,/href="\/audit\/ui-fixture"/);
 assert.doesNotMatch(rawRender(createElement(AuditResult,{audit:fixture('consistent'),replay:true})),/Open result link/);
});

test('stable test selectors survive language switching and identify audit controls and result blocks',()=>{
 for(const lang of ['en','zh']){const page=rawRender(createElement(LanguageProvider,{value:lang},createElement(AuditPage,{api:createApi('',async()=>Response.json({}))})));for(const id of ['audit-submit','audit-load','audit-import-json','audit-video-input','audit-model','audit-id'])assert.match(page,new RegExp('data-testid="'+id+'"'));
 const result=rawRender(createElement(LanguageProvider,{value:lang},createElement(AuditResult,{audit:fixture('consistent')})));for(const id of ['audit-result','audit-verdict','audit-events','audit-export-json','audit-export-markdown'])assert.match(result,new RegExp('data-testid="'+id+'"'));}
});

test('pendulum uses optional user length and preserves backend periods in saved replay',async()=>{
let body;const api=createApi('',async(u,i)=>{body=i.body;return Response.json({})});await api.audit(new File(['fixture'],'p.mp4'),0,5,true,undefined,'pendulum',undefined,0.7);assert.equal(body.get('length_m'),'0.7');assert.equal(body.get('assumed_model'),'pendulum');
const a={...fixture('consistent'),assumed_model:'pendulum',length_m:0.7,numbers:{period_s:1.23456,implied_length_m:0.76543,predicted_period_s:1.54321}};assert.deepEqual(parseSavedAudit(JSON.stringify(a)),a);const html=render(createElement(AuditResult,{audit:a,replay:true}));for(const t of ['單擺運動','1.23456','0.76543','1.54321'])assert.ok(html.includes(t));assert.throws(()=>parseSavedAudit(JSON.stringify({...a,length_m:-1})));
});

test('bounce chart sorts backend ratio indices and renders a reference and accessible data',async()=>{const {BounceChart}=await import('../.test-dist/BounceChart.js');const html=rawRender(createElement(BounceChart,{numbers:{rebound_ratio_2:1.23456,rebound_ratio_1:.654321,other:99}}));assert.match(html,/Rebound height ratios/);assert.match(html,/1.0/);assert.ok(html.indexOf('rebound_ratio_1')<html.indexOf('rebound_ratio_2'));assert.match(html,/title="1.23456"/);assert.doesNotMatch(html,/other/);assert.match(html,/tolerance/)});

test('interview source labels distinguish real model questions from fixed mock questions',async()=>{const {InterviewQuestions}=await import('../.test-dist/InterviewPanel.js');for(const source of ['mock','model']){const html=rawRender(createElement(InterviewQuestions,{draft:{draft_id:'fixture',video_url:'',interview:{source,note:'fixture note',questions:[{field:'camera_static',text:'fixture question'}]}}}));assert.match(html,/fixture question/);assert.match(html,/fixture note/);assert.match(html,source==='mock'?/Fixed questions \(mock\)/:/Questions by Muse Spark/);if(source==='mock')assert.doesNotMatch(html,/Questions by Muse Spark/)}});

test('reviewer-facing English copy avoids provenance labels and internal test terminology',async()=>{
 const {Home}=await import('../.test-dist/Home.js');const a={...fixture('consistent'),audit_id:'example',reasons:['Observed motion fits the assumed model.'],limits:['Fixed camera required.'],synthetic:true};
 const html=rawRender(createElement(AuditResult,{audit:a,replay:true}))+rawRender(createElement(Home));assert.doesNotMatch(html,/\b(real|fake|detect|fixture)\b|AI-generated|draft id/i);assert.match(html,/Consistent with free flight on Earth/);assert.match(html,/SYNTHETIC/);
});

test('slow-motion answers preserve yes, no and unknown with verbatim backend refusal',async()=>{const {auditMarkdown}=await import('../.test-dist/auditReport.js');const {physicsCardLines}=await import('../.test-dist/cardExport.js');for(const value of [true,false,null,undefined]){const a={...fixture('insufficient_data'),slow_motion:value,reasons:['slow motion: timing cannot be checked at 0.123456 s']};const html=rawRender(createElement(AuditResult,{audit:a,replay:true}));const label=value===true?'Yes':value===false?'No':'Not provided';assert.ok(html.includes(label));assert.ok(physicsCardLines(a).join(' ').includes(label));assert.match(auditMarkdown(a),/Slow motion/);assert.match(html,/slow motion: timing cannot be checked at 0.123456 s/);assert.equal(parseSavedAudit(JSON.stringify(a)).slow_motion,value)}assert.throws(()=>parseSavedAudit(JSON.stringify({...fixture('consistent'),slow_motion:'true'})))});

test('validated explanation text and source pass unchanged through result and exports',async()=>{const {physicsCardLines}=await import('../.test-dist/cardExport.js');const {auditMarkdown}=await import('../.test-dist/auditReport.js');for(const source of ['template','model']){const a={...fixture('consistent'),explanation:{source,text:'Measured value: 0.123456789'}};assert.deepEqual(parseSavedAudit(JSON.stringify(a)).explanation,a.explanation);const html=rawRender(createElement(AuditResult,{audit:a,replay:true}));assert.match(html,/0.123456789/);assert.ok(physicsCardLines(a).includes(a.explanation.text));assert.ok(auditMarkdown(a).includes(a.explanation.text));assert.match(html,source==='model'?/Generated by Muse Spark/:/Fixed template/)}assert.throws(()=>parseSavedAudit(JSON.stringify({...fixture('consistent'),explanation:{source:'unknown',text:'x'}})))});

test('gravity ruler uses backend value and range with fixed reference constants',async()=>{const {GravityRuler,gravityBodies}=await import('../.test-dist/GravityRuler.js');assert.deepEqual(gravityBodies.find(p=>p[0]==='Earth'),['Earth',9.81]);const html=rawRender(createElement(GravityRuler,{numbers:{g_apparent_m_s2:2,g_apparent_low:1.4,g_apparent_high:2.6}}));for(const text of ['Pluto','Jupiter','1.4','2.6','logarithmic'])assert.ok(html.includes(text));assert.doesNotMatch(rawRender(createElement(GravityRuler,{numbers:{}})),/<svg/)});

test('audit charts expose text alternatives and native keyboard controls',()=>{const a={...fixture('consistent'),numbers:{g_apparent_m_s2:9.81},points:[[0,1,2],[1,3,4]],ghost_points:[[0,1,2],[1,3,8]]};const html=rawRender(createElement(AuditResult,{audit:a,replay:true}));assert.match(html,/role="img"/);assert.match(html,/Apparent g:/);assert.match(html,/Play recorded points/);assert.match(html,/type="range"/);assert.match(html,/aria-label="Recorded-point playback/)});

test('processing feedback never invents backend phase percentages',async()=>{const {AuditProgress}=await import('../.test-dist/AuditProgress.js');const html=rawRender(createElement(AuditProgress,{percent:100}));assert.match(html,/Separate phase progress is not reported/);assert.match(html,/<progress aria-label=/);assert.doesNotMatch(html,/value="100"/);assert.match(rawRender(createElement(AuditProgress,{percent:25})),/value="25"/)});

test('print report includes verdict, explanation, measurements, track and limits',async()=>{const {PrintReport}=await import('../.test-dist/PrintReport.js');const html=rawRender(createElement(PrintReport,{audit:{...fixture('consistent'),explanation:{source:'template',text:'saved explanation'}}}));for(const text of ['Print A4 report','saved explanation','Fixed template','sentinel','fixture limitation'])assert.ok(html.includes(text));assert.match(html,/aria-hidden="true"/)});

test('voice input stays unavailable without Meta API and proposals require field confirmation',async()=>{const {VoiceAnswers}=await import('../.test-dist/VoiceAnswers.js');const html=rawRender(createElement(VoiceAnswers,{}));assert.match(html,/requires Meta API/);assert.match(html,/disabled/);assert.match(html,/No microphone access/);const review=rawRender(createElement(VoiceAnswers,{proposal:{transcript:'user transcript',fields:[{label:'Measured size',value:'0.11'}]},onConfirm:()=>{throw Error('not during render')}}));assert.match(review,/user transcript/);assert.match(review,/value="0.11"/);assert.match(review,/data-testid="voice-confirm" disabled/)});

test('all supported model verdicts use consistent reviewer-facing English',async()=>{const {verdictEnglish}=await import('../.test-dist/audit.js');for(const assumed_model of ['free_flight','bounce','pendulum'])for(const verdict of ['consistent','inconsistent','insufficient_data']){const t=verdictEnglish({assumed_model,verdict});assert.match(t,/with the assumed .* model$/);assert.doesNotMatch(t,/insufficient_data|free_flight|detect|fake/)}});

test('window confirmation requires explicit valid bounds within the video duration',async()=>{const {validWindow}=await import('../.test-dist/WindowSelector.js');assert.ok(validWindow('0.10','1.23',2));for(const [s,e,d] of [['','1',2],['1','1',2],['0','3',2],['0','1',0],['NaN','1',2]])assert.equal(validWindow(s,e,d),false)});

test('public audit paths safely round-trip IDs and share links exclude local drafts',async()=>{const {auditIdFromPath,shareAuditUrl}=await import('../.test-dist/experiment.js');assert.equal(auditIdFromPath('/audit/a%2Fb'),'a/b');assert.equal(auditIdFromPath('/audit/%ZZ'),null);assert.equal(auditIdFromPath('/audit/'),null);assert.equal(shareAuditUrl('a/b','https://example.test'),'https://example.test/audit/a%2Fb')});

test('model headlines remain verbatim in either language and all exports; null retains fallback',async()=>{const {physicsCardLines}=await import('../.test-dist/cardExport.js');const {auditMarkdown}=await import('../.test-dist/auditReport.js');for(const text of ['Home','Value 0.123456789 <span>']){const a={...fixture('consistent'),headline:{source:'model',text}};assert.deepEqual(parseSavedAudit(JSON.stringify(a)).headline,a.headline);for(const lang of ['en','zh']){const html=rawRender(createElement(LanguageProvider,{value:lang},createElement(AuditResult,{audit:a,replay:true})));assert.match(html,/data-testid="model-headline"/);assert.ok(html.includes(text.replaceAll('<','&lt;').replaceAll('>','&gt;')))}assert.equal(physicsCardLines(a)[0],text);assert.ok(auditMarkdown(a).includes(text))}for(const headline of [null,undefined]){const a={...fixture('consistent'),headline};assert.doesNotMatch(rawRender(createElement(AuditResult,{audit:a,replay:true})),/data-testid="model-headline"/);assert.doesNotMatch(physicsCardLines(a).join(' '),/Written by Muse Spark|awaiting/)}assert.throws(()=>parseSavedAudit(JSON.stringify({...fixture('consistent'),headline:{source:'template',text:'x'}})))});

test('model usage uses actual sources and never infers interview provenance for archives',async()=>{const {modelUsage}=await import('../.test-dist/ModelUsage.js');let text=modelUsage({...fixture('consistent'),track_source:'color',explanation:{source:'template',text:'x'},headline:null}).flat().join(' ');assert.match(text,/Not recorded/);assert.doesNotMatch(text,/Muse Spark|SAM 3.1/);assert.match(text,/no model used/);text=modelUsage({...fixture('consistent'),track_source:'sam',explanation:{source:'model',text:'x'},headline:{source:'model',text:'x'}},'model').flat().join(' ');assert.match(text,/SAM 3.1/);assert.equal(text.match(/Muse Spark/g).length,3)});

test('retake hints are fixed mappings for insufficient data only and keep original reasons',async()=>{const {retakeTips,RetakeGuide}=await import('../.test-dist/RetakeGuide.js');assert.deepEqual(retakeTips(['camera is not static; this check needs a fixed camera']).map(r=>r.id),['camera']);assert.deepEqual(retakeTips(['user says slow motion']).map(r=>r.id),['timing']);assert.ok(retakeTips(['object size changes and moves towards the camera']).some(r=>r.id==='perspective'));assert.deepEqual(retakeTips(['unknown observation']),[]);assert.equal(rawRender(createElement(RetakeGuide,{verdict:'inconsistent',reasons:['slow motion']})),'');const html=rawRender(createElement(RetakeGuide,{verdict:'insufficient_data',reasons:['measured 0.123456 s']}));assert.match(html,/measured 0.123456 s/);assert.match(html,/no model used/)});

test('interview is the expanded primary flow while direct audit and JSON import remain collapsed',()=>{const html=rawRender(createElement(AuditPage,{api:createApi('',async()=>Response.json({}))}));const tag=id=>html.match(new RegExp('<details[^>]*data-testid="'+id+'"[^>]*>'))?.[0];assert.match(tag('interview-panel'),/\bopen(?:="")?/);assert.doesNotMatch(tag('advanced-audit'),/\bopen/);assert.doesNotMatch(tag('offline-import'),/\bopen/);assert.ok(html.indexOf('data-testid="interview-panel"')<html.indexOf('data-testid="capture-checklist"'));assert.ok(html.indexOf('data-testid="interview-video"')<html.indexOf('data-testid="audit-video-input"'));for(const id of ['interview-prepare','audit-submit','audit-import-json'])assert.ok(html.includes('data-testid="'+id+'"'));assert.match(html,/Advanced: check without the interview/)});

test('result summary uses the correct colour class and puts all three outcomes before untouched evidence',async()=>{const {readFile}=await import('node:fs/promises');const css=await readFile(new URL('./style.css',import.meta.url),'utf8');for(const [verdict,colour] of Object.entries({consistent:'#185b3a',inconsistent:'#8b3e0b',insufficient_data:'#4e5960'})){const a={...fixture(verdict),headline:{source:'model',text:'Headline 0.123456'},explanation:{source:'model',text:'Explanation 0.123456'},reasons:['Reason 0.123456']};const before=JSON.stringify(a),html=rawRender(createElement(AuditResult,{audit:a,replay:true}));assert.ok(html.includes('verdict-'+verdict));assert.ok(css.includes('.verdict-'+verdict+'{background:'+colour+'}'));const sequence=['data-testid="audit-verdict"','Headline 0.123456','Explanation 0.123456','data-testid="audit-reasons"','data-testid="audit-details"'];for(let i=1;i<sequence.length;i++)assert.ok(html.indexOf(sequence[i-1])<html.indexOf(sequence[i]));const details=html.match(/<details[^>]*data-testid="audit-details"[^>]*>/)[0];assert.doesNotMatch(details,/\bopen/);assert.match(html,/123.456789/);assert.equal(JSON.stringify(a),before)}});
