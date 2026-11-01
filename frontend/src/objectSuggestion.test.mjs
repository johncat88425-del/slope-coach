import test from 'node:test';
import assert from 'node:assert/strict';
import {createElement} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {createApi} from '../.test-dist/api.js';
import {ObjectSuggestionHint,suggestedObjectName,suggestedVehicleFields} from '../.test-dist/ObjectSuggestion.js';
import {LanguageProvider} from '../.test-dist/i18n.js';

const suggestion={source:'muse-spark-1.3',object_name:'orange ball',camera_looks_static:true,reason:'Please check the camera in the original clip.'};
test('suggestion prefills the name while edited names remain the submitted answer',async()=>{
 const calls=[];
 const api=createApi('',async(url,init)=>{calls.push([url,init.body]);return Response.json({draft_id:'one',suggestion})});
 const draft=await api.auditDraft(new File(['clip'],'clip.mp4'));
 assert.equal(suggestedObjectName('ball',false,draft.suggestion),'orange ball');
 const edited=suggestedObjectName('wooden block',true,draft.suggestion);
 assert.equal(edited,'wooden block');
 await api.auditFromDraft(draft.draft_id,{object_name:edited,camera_static:false,t_start:0,t_end:1,assumed_model:'free_flight'});
 assert.equal(calls[1][1].get('object_name'),'wooden block');
 assert.equal(calls[1][1].get('camera_static'),'false');
 assert.equal(suggestedObjectName('ball',false,null),'ball');
 assert.equal(suggestedObjectName('my object',true,null),'my object');
});
test('camera suggestions are text only and absent suggestions render nothing',()=>{
 assert.equal(render(createElement(ObjectSuggestionHint,{suggestion:null})), '');
 assert.equal(render(createElement(ObjectSuggestionHint,{})), '');
 for(const fixed of [true,false,null]){
  const html=render(createElement(ObjectSuggestionHint,{suggestion:{...suggestion,camera_looks_static:fixed}}));
  assert.match(html,/Suggested by Muse Spark — please check/);
  assert.ok(html.includes(suggestion.reason));
  assert.doesNotMatch(html,/<input|<select|checked=/);
  if(fixed===true)assert.match(html,/camera looks fixed/);
  if(fixed===false)assert.match(html,/camera may be moving/);
 }
});
test('vehicle suggestions prefill only the model and class, preserving fields the user has edited',()=>{
 const car={...suggestion,assumed_model:'vehicle',vehicle_class:'sedan',judgeable:false},before=JSON.stringify(car);
 const current={model:'',vehicleClass:''},untouched={model:false,vehicleClass:false};
 assert.deepEqual(suggestedVehicleFields(current,untouched,car),{model:'vehicle',vehicleClass:'sedan'});
 assert.deepEqual(suggestedVehicleFields({model:'bounce',vehicleClass:''},{model:true,vehicleClass:false},car),{model:'bounce',vehicleClass:''});
 assert.deepEqual(suggestedVehicleFields({model:'vehicle',vehicleClass:'pickup'},{model:false,vehicleClass:true},car),{model:'vehicle',vehicleClass:'pickup'});
 assert.deepEqual(suggestedVehicleFields(current,untouched,{...car,vehicle_class:null}),{model:'vehicle',vehicleClass:''});
 assert.deepEqual(suggestedVehicleFields(current,untouched,{...car,vehicle_class:'invalid'}),{model:'vehicle',vehicleClass:''});
 for(const value of [undefined,null,suggestion])assert.deepEqual(suggestedVehicleFields(current,untouched,value),current);
 assert.equal(JSON.stringify(car),before);assert.deepEqual(Object.keys(suggestedVehicleFields(current,untouched,car)).sort(),['model','vehicleClass']);
});
test('negative Spark prechecks show an advisory with verbatim reasons, never disabling confirmation',()=>{
 for(const language of ['en','zh']){
  const value={...suggestion,judgeable:false,reason:'Details'},before=JSON.stringify(value);
  const html=render(createElement(LanguageProvider,{value:language},createElement(ObjectSuggestionHint,{suggestion:value})));
  assert.match(html,/data-testid="spark-precheck"/);assert.match(html,/role="status"/);assert.match(html,/precheck-warning/);assert.match(html,/Details/);
  assert.match(html,language==='zh'?/Muse Spark 認為這支片可能無法判斷：/:/Muse Spark thinks this clip may not be judgeable:/);
  assert.doesNotMatch(html,/<input|disabled|blocked/);assert.equal(JSON.stringify(value),before);
 }
 for(const judgeable of [undefined,null,true])assert.doesNotMatch(render(createElement(ObjectSuggestionHint,{suggestion:{...suggestion,judgeable}})),/data-testid="spark-precheck"/);
 const empty=render(createElement(ObjectSuggestionHint,{suggestion:{...suggestion,judgeable:false,reason:''}}));
 assert.match(empty,/may not be judgeable\./);assert.doesNotMatch(empty,/undefined|null/);
});
