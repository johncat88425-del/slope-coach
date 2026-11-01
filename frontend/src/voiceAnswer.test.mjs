import test from 'node:test';
import assert from 'node:assert/strict';
import {createElement} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {createApi,ApiError,serverBusyMessage} from '../.test-dist/api.js';
import {VoiceAnswers,VoiceReview} from '../.test-dist/VoiceAnswers.js';
import {parseVoiceAnswer,voiceFieldPatch,voiceAudioFile} from '../.test-dist/voiceAnswer.js';
import {startVoiceRecording,MAX_VOICE_BYTES} from '../.test-dist/voiceRecorder.js';
import {LanguageProvider} from '../.test-dist/i18n.js';

const proposal={source:{transcript:'muse-voice-transcribe-1.0',fields:'muse-spark-1.3'},transcript:'My measured size is 0.067123 metres.',fields:{camera_static:{value:false,confirmed:false},slow_motion:{value:true,confirmed:false},object_size_m:{value:0.067123,confirmed:false},length_m:{value:0.250123,confirmed:false},assumed_model:{value:'pendulum',confirmed:false},time_window:{value:[0.03123,1.25678],confirmed:false}}};
test('voice upload uses the draft-specific multipart endpoint; response alone never submits an audit',async()=>{
 const calls=[];const api=createApi('http://localhost:8000/',async(url,init)=>{calls.push([url,init]);return Response.json(proposal)});
 const audio=voiceAudioFile(new Blob(['recording'],{type:'audio/mp4;codecs=mp4a.40.2'}));
 const response=parseVoiceAnswer(await api.voiceAnswer('draft / one',audio));
 assert.equal(calls.length,1);assert.equal(calls[0][0],'http://localhost:8000/api/audit-drafts/draft%20%2F%20one/voice');
 assert.equal(calls[0][1].method,'POST');assert.deepEqual([...calls[0][1].body.keys()],['audio']);
 assert.equal(calls[0][1].body.get('audio').name,'answer.m4a');assert.equal(await calls[0][1].body.get('audio').text(),'recording');
 assert.deepEqual(response,proposal);
 const html=render(createElement(VoiceReview,{answer:response,onUse(){throw Error('must only run on a click')}}));
 assert.equal((html.match(/>Use this /g)||[]).length,6);assert.match(html,/Transcribed by Muse Voice Transcribe/);assert.match(html,/Fields suggested by Muse Spark/);assert.match(html,/0.067123/);assert.match(html,/0.03123 – 1.25678/);assert.doesNotMatch(html,/<form|checked=/);
});
test('each accepted voice field changes only its matching form values, without rounding or window confirmation',()=>{
 const original={camera:'yes',slow:'no',model:'free_flight',size:'',length:'',start:'',end:'',windowConfirmed:false};
 let form={...original};
 // Receiving or displaying the proposal has no effect on the form.
 parseVoiceAnswer(proposal);assert.deepEqual(form,original);
 form={...form,...voiceFieldPatch('object_size_m',proposal.fields.object_size_m.value)};
 assert.deepEqual(form,{...original,size:'0.067123'});
 form={...form,...voiceFieldPatch('time_window',proposal.fields.time_window.value)};
 assert.equal(form.start,'0.03123');assert.equal(form.end,'1.25678');assert.equal(form.windowConfirmed,false);assert.equal(form.camera,'yes');
 assert.deepEqual(voiceFieldPatch('camera_static',false),{camera:'no'});
 assert.deepEqual(voiceFieldPatch('slow_motion',true),{slow:'yes'});
 assert.deepEqual(voiceFieldPatch('length_m',0.250123),{length:'0.250123'});
 assert.deepEqual(voiceFieldPatch('assumed_model','pendulum'),{model:'pendulum'});
 for(const [field,value] of [['camera_static','true'],['object_size_m',0],['length_m',Infinity],['time_window',[2,1]],['time_window',[0,NaN]],['assumed_model','invented'],['object_name','ball']])assert.equal(voiceFieldPatch(field,value),null);
});
test('mock answers show no model attribution or applicable fields and keep recording disabled',()=>{
 const answer=parseVoiceAnswer({...proposal,source:{transcript:'mock',fields:'mock'}});
 assert.deepEqual(answer.fields,{});
 const review=render(createElement(VoiceReview,{answer,onUse(){throw Error('no apply')}}));assert.doesNotMatch(review,/Use this|Transcribed by Muse|Fields suggested by Muse/);
 const mock=render(createElement(VoiceAnswers,{api:createApi(),draftId:'one',source:'mock',onUse(){}}));
 assert.match(mock,/data-testid="voice-record" disabled/);assert.match(mock,/requires Meta API/);assert.doesNotMatch(mock,/<audio|voice-send/);
 for(const changed of [{fields:{object_size_m:{value:0.1,confirmed:true}}},{fields:{time_window:{value:[0,0],confirmed:false}}},{source:{}},{transcript:null}])assert.throws(()=>parseVoiceAnswer({...proposal,...changed}),/unreadable voice answer/);
});
test('voice gateway errors use a safe message and never retry; demo mode does not fetch',async()=>{
 let calls=0;const audio=new File(['audio'],'answer.webm');
 const api=createApi('',async()=>{calls++;return Response.json({detail:'voice model unavailable: example'},{status:502})});
 await assert.rejects(api.voiceAnswer('one',audio),e=>e instanceof ApiError&&e.status===502&&e.message===serverBusyMessage);assert.equal(calls,1);
 const demo=createApi('',async()=>{throw Error('must not fetch')},{demoOnly:true});await assert.rejects(demo.voiceAnswer('one',audio),/demo/i);
});
test('review labels translate while the transcript and numeric values remain verbatim',()=>{
 const html=render(createElement(LanguageProvider,{value:'zh'},createElement(VoiceReview,{answer:proposal,onUse(){}})));
 assert.match(html,/由 Muse Voice Transcribe 轉錄/);assert.match(html,/採用此欄/);assert.ok(html.includes(proposal.transcript));assert.match(html,/0.067123/);
});

function fakeRecorder(){let released=0,recorder;return {get released(){return released},get recorder(){return recorder},options:{getStream:async()=>({getTracks:()=>[{stop(){released++}}]}),makeRecorder(){recorder={state:'inactive',mimeType:'audio/webm',start(){this.state='recording'},stop(){this.state='inactive';this.ondataavailable({data:new Blob(['audio'],{type:'audio/webm'})});this.onstop()}};return recorder}}}}
test('recording starts only explicitly, finishes as audio, and releases microphone tracks',async()=>{
 const fake=fakeRecorder();assert.equal(fake.recorder,undefined);
 const session=await startVoiceRecording(fake.options);assert.equal(fake.recorder.state,'recording');assert.equal(fake.released,0);
 const blob=await session.stop();assert.equal(await blob.text(),'audio');assert.equal(blob.type,'audio/webm');assert.equal(fake.released,1);
 session.cancel();assert.equal(fake.released,1);
});
test('cancellation, recorder failure and the upload-size limit all release the microphone',async()=>{
 const cancelled=fakeRecorder();const session=await startVoiceRecording(cancelled.options);session.cancel();await assert.rejects(session.finished,/cancelled/);assert.equal(cancelled.released,1);
 const oversized=fakeRecorder();const large=await startVoiceRecording(oversized.options);oversized.recorder.ondataavailable({data:new Blob([new Uint8Array(MAX_VOICE_BYTES+1)])});await assert.rejects(large.finished,/larger than 10 MB/);assert.equal(oversized.released,1);
 const failed=fakeRecorder();const failure=await startVoiceRecording(failed.options);failed.recorder.onerror();await assert.rejects(failure.finished,/recording failed/);assert.equal(failed.released,1);
 const unavailable=fakeRecorder();await assert.rejects(startVoiceRecording({...unavailable.options,makeRecorder(){throw Error('unsupported')}}),/unsupported/);assert.equal(unavailable.released,1);
 await assert.rejects(startVoiceRecording({getStream:async()=>{throw Error('permission denied')}}),/permission denied/);
});
