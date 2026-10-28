import test from 'node:test';
import assert from 'node:assert/strict';
import {createApi,ApiError} from '../.test-dist/api.js';
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
