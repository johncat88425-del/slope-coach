import test from 'node:test';
import assert from 'node:assert/strict';
import {createApi,ApiError,friendlyApiError,uploadAudit} from '../.test-dist/api.js';
test('multipart uploads use documented names and let fetch supply boundary',async()=>{
 const calls=[]; const api=createApi('http://localhost:8000/',async(url,init)=>{calls.push({url,init});return Response.json({trial_id:'trial'})});
 const file=new File(['ui test fixture'],'clip.mp4',{type:'video/mp4'});
 await api.trial('e 1','baseline',3,file);
 assert.equal(calls[0].url,'http://localhost:8000/api/experiments/e%201/trials');
 assert.equal(calls[0].init.body.get('kind'),'baseline');
 assert.equal(calls[0].init.body.get('calibration_version'),'3');
 assert.equal(calls[0].init.body.get('file').name,'clip.mp4');
 assert.equal(calls[0].init.headers,undefined);
 await api.photo('e',file);assert.match(calls[1].url,/\/scene-photo$/);
});
test('prediction is created with version refs; comparison preserves locked IDs',async()=>{
 const calls=[]; const api=createApi('',async(url,init)=>{calls.push({url,init});return Response.json({})});
 await api.predict('e',2,1,0.8); await api.compare('e','p-old','t-new');
 assert.equal(calls[0].init.method,'POST');
 assert.deepEqual(JSON.parse(calls[0].init.body),{calibration_version:2,baseline_version:1,distance_m:0.8});
 assert.deepEqual(JSON.parse(calls[1].init.body),{prediction_id:'p-old',trial_id:'t-new'});
 assert.equal(calls[1].url,'/api/experiments/e/comparisons');
});
test('501/409/422 errors expose backend reason and never retry mutations',async()=>{
 for(const status of [501,409,422]){
  let calls=0;const api=createApi('',async()=>{calls++;return Response.json({detail:'explicit backend reason'},{status})});
  await assert.rejects(api.track('t'),e=>e instanceof ApiError&&e.status===status&&e.message==='explicit backend reason');
  assert.equal(calls,1);
 }
});
test('validation details and insufficient-data responses remain available to UI',async()=>{
 const api=createApi('',async()=>Response.json({detail:[{loc:['body','slope_height_m'],msg:'invalid'}]},{status:422}));
 await assert.rejects(api.calibration('e',{}),e=>e.message.includes('slope_height_m'));
 const result={verdict:'insufficient_data',checks:[{passed:false,blocking:true,detail:'missing release'}],can_still_say:['later motion visible']};
 const valid=createApi('',async()=>Response.json(result));assert.deepEqual(await valid.compare('e','p','t'),result);
});
test('manual detections retain missing frames and source, release time requires explicit PUT',async()=>{
 const calls=[];const api=createApi('',async(url,init)=>{calls.push({url,init});return Response.json({})});
 const detections=[{t_s:1,centroid_px:null,source:'manual'}];
 await api.detections('t',detections);await api.release('t',0);
 assert.deepEqual(JSON.parse(calls[0].init.body),{detections});assert.equal(calls[0].init.method,'PUT');
 assert.deepEqual(JSON.parse(calls[1].init.body),{t0_s:0});
});
test('report download preserves plain text and format-specific endpoint',async()=>{
 let path;const api=createApi('',async(url)=>{path=url;return new Response('trial_id,t_s\n')});
 assert.equal(await api.report('e','csv'),'trial_id,t_s\n');assert.equal(path,'/api/experiments/e/report.csv');
});

test('friendly errors distinguish 404 and 422 without changing backend reasons or numbers',()=>{
 assert.match(friendlyApiError(new ApiError(404,'missing 123.456')),/Result not found.*missing 123.456/);assert.match(friendlyApiError(new ApiError(422,'size 0.123456')),/check the submitted settings.*size 0.123456/);
});
test('XHR upload progress measures bytes only, then waits for backend result without retry',async()=>{
 let x,sends=0;const updates=[];const factory=()=>x={upload:{},open(method,url){assert.equal(method,'POST');assert.equal(url,'/api/audits')},send(){sends++}};
 const pending=uploadAudit('/api/audits',new FormData(),v=>updates.push(v),factory);x.upload.onprogress({lengthComputable:true,loaded:25,total:100});x.upload.onload();assert.deepEqual(updates,[0,25,100]);x.status=200;x.responseText='{"audit_id":"fixture"}';x.onload();assert.deepEqual(await pending,{audit_id:'fixture'});assert.equal(sends,1);
 const failed=uploadAudit('/api/audits',new FormData(),()=>{},factory);x.status=422;x.responseText='{"detail":"bad 0.123456"}';x.onload();await assert.rejects(failed,e=>e.status===422&&e.message==='bad 0.123456');
 const network=uploadAudit('/api/audits',new FormData(),()=>{},factory);x.onerror();await assert.rejects(network,/Cannot connect/);
});

test('interview prepares a file then submits confirmed answers with a single-use draft, never file again',async()=>{const calls=[];const api=createApi('',async(url,i)=>{calls.push([url,i.body]);return Response.json({})});await api.auditDraft(new File(['fixture'],'clip.mp4'));await api.auditFromDraft('draft-1',{t_start:0,t_end:2,camera_static:false,slow_motion:true,assumed_model:'pendulum',length_m:.25});assert.equal(calls[0][0],'/api/audit-drafts');assert.ok(calls[0][1].has('file'));assert.equal(calls[1][0],'/api/audit-jobs');assert.equal(calls[1][1].get('draft_id'),'draft-1');assert.equal(calls[1][1].has('file'),false);assert.equal(calls[1][1].get('slow_motion'),'true');assert.equal(calls[1][1].get('camera_static'),'false');assert.equal(calls[1][1].get('length_m'),'0.25');assert.equal(calls[1][1].has('object_size_m'),false)});

test('object prompt defaults to ball and custom names pass unchanged to both audit paths',async()=>{let body;const api=createApi('',async(u,i)=>{body=i.body;return Response.json({})});await api.audit(new File(['fixture'],'clip.mp4'),0,1,true);assert.equal(body.get('object_name'),'ball');await api.audit(new File(['fixture'],'clip.mp4'),0,1,true,undefined,'bounce',undefined,undefined,'red cube');assert.equal(body.get('object_name'),'red cube');await api.auditFromDraft('d',{t_start:0,t_end:1,camera_static:true,slow_motion:false,assumed_model:'bounce',object_name:'red cube'});assert.equal(body.get('object_name'),'red cube')});

test('window suggestions use the documented draft endpoint and object prompt',async()=>{let path,init;const api=createApi('',async(p,i)=>{path=p;init=i;return Response.json({windows:[],source:'physics'})});await api.flightWindows('d/1','orange ball');assert.equal(path,'/api/audit-drafts/d%2F1/windows');assert.equal(init.method,'POST');assert.equal(init.body.get('object_name'),'orange ball')});

test('demo-only API guard blocks reads and uploads before any network or XHR use',async()=>{let calls=0;const api=createApi('',async()=>{calls++;throw Error('network must remain unused')},{demoOnly:true});for(const promise of [api.getAudit('x'),api.create('x'),api.auditDraft(new File(['x'],'x.mp4')),api.audit(new File(['x'],'x.mp4'),0,1,true,undefined,'free_flight',()=>{})])await assert.rejects(promise,/Demo mode cannot upload/);assert.equal(calls,0)});
