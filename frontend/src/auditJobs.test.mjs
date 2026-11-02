import test from 'node:test';
import assert from 'node:assert/strict';
import {createApi,jobLostMessage} from '../.test-dist/api.js';

function server(states){const calls=[];let i=0;return {calls,transport:async(url,init={})=>{calls.push([url,init.method||'GET']);
 if((init.method||'GET')==='POST')return Response.json({job_id:'job_1',status:'running'},{status:202});
 const s=states[Math.min(i++,states.length-1)];if(s==='down')throw new TypeError('network');if(typeof s==='number')return new Response('{"detail":"x"}',{status:s});return Response.json(s)}}}

test('T246: a check is submitted as a job and polled until the result arrives',async()=>{
 const audit={audit_id:'aud_1',verdict:'consistent'};const s=server([{status:'running'},'down',{status:'done',audit}]);
 const r=await createApi('',s.transport,{pollMs:1}).auditFromDraft('d',{t_start:0,t_end:1,camera_static:true,assumed_model:'free_flight'});
 assert.deepEqual(r,audit);assert.equal(s.calls[0][0],'/api/audit-jobs');assert.equal(s.calls[1][0],'/api/audit-jobs/job_1');
});
test('T246: a failed job shows its reason; a lost job asks to resubmit; five network misses give up',async()=>{
 const opts={pollMs:1};
 await assert.rejects(createApi('',server([{status:'failed',error:'bad window',status_code:422}]).transport,opts).auditFromDraft('d',{t_start:0,t_end:1,camera_static:true,assumed_model:'free_flight'}),e=>e.status===422&&e.message==='bad window');
 await assert.rejects(createApi('',server([404]).transport,opts).auditFromDraft('d',{t_start:0,t_end:1,camera_static:true,assumed_model:'free_flight'}),e=>e.message===jobLostMessage);
 const s=server(['down']);await assert.rejects(createApi('',s.transport,opts).auditFromDraft('d',{t_start:0,t_end:1,camera_static:true,assumed_model:'free_flight'}));
 assert.equal(s.calls.length,6);
});
