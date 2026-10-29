import test from 'node:test';
import assert from 'node:assert/strict';
import {createElement} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {createApi} from '../.test-dist/api.js';
import {ObjectSuggestionHint,suggestedObjectName} from '../.test-dist/ObjectSuggestion.js';

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
