import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {pointFromPointer,pointFromKey,serializeTrackingPoint} from '../.test-dist/trackingPoint.js';
import {TrackingPointPicker} from '../.test-dist/TrackingPointPicker.js';
import {LanguageProvider,translateText} from '../.test-dist/i18n.js';
import {createApi} from '../.test-dist/api.js';

test('pointer positions map to native pixels for scaled 1080p and 4K frames, including origin and final pixel',()=>{
 const rect={left:40,top:20,width:480,height:270};
 assert.deepEqual(pointFromPointer(280,155,rect,{width:1920,height:1080}),[960,540,0]);
 assert.deepEqual(pointFromPointer(280,155,rect,{width:3840,height:2160}),[1920,1080,0]);
 assert.deepEqual(pointFromPointer(40,20,rect,{width:3840,height:2160}),[0,0,0]);
 assert.deepEqual(pointFromPointer(520,290,rect,{width:1920,height:1080}),[1919,1079,0]);
});

test('letterboxing and portrait pillarboxing are excluded from selectable image content',()=>{
 const rect={left:10,top:30,width:400,height:400};
 assert.equal(pointFromPointer(210,40,rect,{width:1920,height:1080}),undefined);
 assert.deepEqual(pointFromPointer(210,230,rect,{width:1920,height:1080}),[960,540,0]);
 assert.equal(pointFromPointer(20,230,rect,{width:1080,height:1920}),undefined);
 assert.deepEqual(pointFromPointer(210,230,rect,{width:1080,height:1920}),[540,960,0]);
 for(const point of [[-1,230],[500,230],[210,500],[NaN,230]])assert.equal(pointFromPointer(...point,rect,{width:1920,height:1080}),undefined);
 for(const size of [{width:0,height:0},{width:Infinity,height:100}])assert.equal(pointFromPointer(1,1,rect,size),undefined);
 assert.equal(pointFromPointer(1,1,{...rect,width:0},{width:1920,height:1080}),undefined);
});

test('keyboard cursor supports coarse movement, single-pixel refinement and image-boundary clamping',()=>{
 const size={width:1920,height:1080};
 assert.deepEqual(pointFromKey('ArrowRight',undefined,size),[982,540,0]);
 assert.deepEqual(pointFromKey('ArrowRight',[0,0,0],size,true),[1,0,0]);
 assert.deepEqual(pointFromKey('ArrowLeft',[0,0,0],size),[0,0,0]);
 assert.deepEqual(pointFromKey('ArrowUp',[0,0,0],size),[0,0,0]);
 assert.deepEqual(pointFromKey('ArrowDown',[1919,1079,0],size),[1919,1079,0]);
 assert.equal(pointFromKey('Enter',undefined,size),undefined);assert.equal(pointFromKey('Tab',undefined,size),undefined);
 assert.equal(pointFromKey('ArrowUp',undefined,{width:0,height:0}),undefined);
});

test('point tuples use JSON rather than comma strings, and malformed coordinates never reach the network',()=>{
 assert.equal(serializeTrackingPoint([0,0,0]),'[0,0,0]');
 for(const point of [[NaN,2,0],[1,Infinity,0],[-1,2,0],[1,2,-1],[1,2,.5],[1,2],[1,2,0,4]])assert.throws(()=>serializeTrackingPoint(point),/Invalid tracking point/);
 let calls=0;const api=createApi('',async()=>{calls++;return Response.json({})});
 assert.throws(()=>api.auditFromDraft('d',{t_start:1,t_end:2,camera_static:true,assumed_model:'free_flight',point_px:[NaN,2,0]}));assert.equal(calls,0);
});

test('draft and direct-upload background requests include exactly the selected native point; optional selection is omitted',async()=>{
 const bodies=[];const api=createApi('',async(url,init)=>{bodies.push(init.body);return Response.json({audit_id:'fixture'})});
 const answers={t_start:2.5,t_end:3.5,camera_static:true,assumed_model:'free_flight'},point=[3000,1200,0];
 await api.auditFromDraft('draft', {...answers,point_px:point});
 await api.audit(new File(['fixture'],'clip.mp4'),2.5,3.5,true,undefined,'free_flight',undefined,undefined,'ball',false,undefined,point);
 await api.auditFromDraft('draft',answers);
 await api.audit(new File(['fixture'],'clip.mp4'),2.5,3.5,true);
 for(const body of bodies.slice(0,2)){assert.deepEqual(JSON.parse(body.get('point_px')),point);assert.equal(body.get('t_start'),'2.5')}
 for(const body of bodies.slice(2))assert.equal(body.has('point_px'),false);
 assert.deepEqual(point,[3000,1200,0]);
});

test('the measured-upload XHR path also carries the same point JSON without changing progress handling',async()=>{
 const previous=globalThis.XMLHttpRequest;let body;
 globalThis.XMLHttpRequest=class{upload={};status=201;responseText='{"audit_id":"fixture"}';open(){}getResponseHeader(){return 'application/json'}send(data){body=data;queueMicrotask(()=>this.onload())}};
 try{await createApi('').audit(new File(['fixture'],'clip.mp4'),1,2,true,undefined,'free_flight',()=>{},undefined,'ball',false,undefined,[22,33,0]);assert.equal(body.get('point_px'),'[22,33,0]')}finally{globalThis.XMLHttpRequest=previous}
});

test('optional first-frame control is labelled, initially disabled until decoded, and localizes all help and states',()=>{
 for(const language of ['en','zh']){
  const html=renderToStaticMarkup(h(LanguageProvider,{value:language},h(TrackingPointPicker,{url:'blob:fixture',start:1.5,onChange(){}})));
  assert.match(html,/data-testid="tracking-point-frame"[^>]*disabled/);assert.match(html,/playsInline|playsinline/);
  assert.doesNotMatch(html,/data-testid="tracking-point-marker"|controls=""/);
  assert.match(html,language==='en'?/optional.*|No tracking point selected/s:/可選/);
  assert.match(html,language==='en'?/Keyboard: arrow keys/:/鍵盤：方向鍵/);
 }
 for(const key of ['Choose the tracking object (optional)','First frame of your confirmed time window. Tap or click the object to mark it. Skip this to track by the object name.','Select tracking object in the first frame','The first frame is unavailable. You can still continue with the object name.','Loading the first frame…','Tracking point selected.','No tracking point selected; the object name will be used.','Cursor position (native pixels):','Clear tracking point','Invalid tracking point. Clear it and select the object again.'])assert.match(translateText(key,'zh'),/[\u3400-\u9fff]/);
});

test('both entry flows invalidate selection when the clip or either window boundary changes, and render only after confirmation',async()=>{
 const [interview,advanced,window,hook]=await Promise.all(['InterviewPanel.tsx','AuditPage.tsx','WindowSelector.tsx','useTrackingPoint.ts'].map(name=>readFile(new URL(name,import.meta.url),'utf8')));
 for(const source of [interview,advanced]){assert.match(source,/useTrackingPoint\([^,]+,start,end,windowConfirmed\)/);assert.match(source,/point=\{point\} onPointChange=\{setPoint\}/)}
 assert.match(window,/valid&&confirmed&&onPointChange/);assert.match(window,/start=\{Number\(start\)\}/);
 assert.match(hook,/\[url,start,end\]/);assert.match(hook,/confirmed&&selection\?\.key===key/);
});
