import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {recordingSteps,moveTourStep,tourKeyDirection} from '../.test-dist/tourSteps.js';
import {TourSlide} from '../.test-dist/TourSlide.js';import {createElement as h} from 'react';import {renderToStaticMarkup as render} from 'react-dom/server';
import {translateText,LanguageProvider} from '../.test-dist/i18n.js';
test('recording sequence follows the six final demo cases without changing saved results',async()=>{
 assert.deepEqual(recordingSteps.map(step=>step.key),['real_own_2','generated_meta_clip4','generated_meta_clip2','synthetic_car_50kmh_braking','synthetic_car_3g_launch','generated_meta_clip4']);
 const verdicts=[];for(const step of recordingSteps){const a=JSON.parse(await readFile(new URL('../../data/demo/'+step.key+'.json',import.meta.url),'utf8')),before=JSON.stringify(a);verdicts.push(a.verdict);const html=render(h(TourSlide,{audit:a,view:step.view}));assert.equal(JSON.stringify(a),before);if(a.synthetic)assert.match(html,/Synthetic test clip/);if(step.view==='ghost'){assert.match(html,/data-testid="tour-ghost"/);assert.match(html,/stroke-dasharray="6 4"/);assert.match(html,/Tracked by SAM 3.1/)}if(step.view==='share')assert.match(html,/data-testid="physics-card-download"/);for(const label of [step.title,step.text])assert.notEqual(translateText(label,'zh'),label)}
 assert.deepEqual(verdicts,['consistent','inconsistent','insufficient_data','consistent','inconsistent','inconsistent']);
});
test('tour keys move one bounded step and preserve form, media and native button keys',()=>{
 assert.equal(moveTourStep(0,-1),0);assert.equal(moveTourStep(5,1),5);assert.equal(moveTourStep(2,1),3);
 for(const key of ['ArrowRight',' ','Spacebar'])assert.equal(tourKeyDirection(key,{tagName:'H2'}),1);
 assert.equal(tourKeyDirection('ArrowLeft',{tagName:'BUTTON'}),-1);
 for(const tagName of ['INPUT','SELECT','TEXTAREA','VIDEO','AUDIO'])assert.equal(tourKeyDirection('ArrowRight',{tagName}),0);
 for(const tagName of ['BUTTON','A','SUMMARY'])assert.equal(tourKeyDirection(' ',{tagName}),0);
 assert.equal(tourKeyDirection('ArrowRight',{isContentEditable:true}),0);assert.equal(tourKeyDirection('ArrowRight',{},true),0);
});
test('missing tour evidence remains explicit and synthetic badges are translated',async()=>{
 assert.match(render(h(TourSlide,{view:'result'})),/unavailable/);
 const a=JSON.parse(await readFile(new URL('../../data/demo/synthetic_car_50kmh_braking.json',import.meta.url),'utf8'));assert.match(render(h(LanguageProvider,{value:'zh'},h(TourSlide,{audit:a,view:'result'}))),/程式模擬測試片/);
});
