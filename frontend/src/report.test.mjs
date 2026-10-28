import test from 'node:test';import assert from 'node:assert/strict';import {auditMarkdown} from '../.test-dist/auditReport.js';
test('audit export preserves backend values and includes evidence, assumptions and limits',()=>{
 const a={audit_id:'fixture',created_at:'date',assumed_model:'free_flight',verdict:'insufficient_data',t_start:1,t_end:2,camera_static:false,object_size_m:null,track_source:'manual',reasons:['a|b'],numbers:{sentinel:0.123456789},points:[[1,3,4]],events:[{t_s:1,kind:'missing',detail:'gap'}],limits:['limit'],video_url:'/media/x',overlay_url:null};
 const report=auditMarkdown(a);assert.match(report,/0\.123456789/);assert.match(report,/not provided/);assert.match(report,/a\\\|b/);assert.match(report,/\| 1 \| 3 \| 4 \|/);assert.match(report,/limit/);assert.match(report,/insufficient_data/);assert.ok(!report.includes('9.81'));
});
