import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';import {createElement as h} from 'react';import {renderToStaticMarkup as render} from 'react-dom/server';
import {AuditProgress} from '../.test-dist/AuditProgress.js';import {RequestStatus} from '../.test-dist/RequestStatus.js';import {analysisStageLabels} from '../.test-dist/AnalysisStages.js';import {LanguageProvider,translateText} from '../.test-dist/i18n.js';
test('both analysis paths show one indeterminate spinner and three unconfirmed workflow descriptions',()=>{
 for(const node of [h(AuditProgress,{percent:100}),h(AuditProgress,{percent:null}),h(RequestStatus,{phase:'checking'})]){
  const html=render(node);assert.equal((html.match(/data-testid="analysis-spinner"/g)||[]).length,1);assert.equal((html.match(/data-state="unreported"/g)||[]).length,3);for(const label of analysisStageLabels)assert.ok(html.includes(label));assert.match(html,/Stage details are unavailable/);assert.doesNotMatch(html,/aria-current|aria-valuenow|<progress|\d+%/);
 }
 for(const phase of ['preparing','scanning','loading','transcribing'])assert.doesNotMatch(render(h(RequestStatus,{phase})),/data-testid="analysis-waiting"/);
});
test('only valid measured upload percentages are displayed; no stage follows a timer',async()=>{
 assert.match(render(h(AuditProgress,{percent:25})),/<progress max="100" value="25"/);
 for(const percent of [NaN,Infinity,-1,101])assert.doesNotMatch(render(h(AuditProgress,{percent})),/<progress|NaN|Infinity|\d+%/);
 const source=await readFile(new URL('./AnalysisStages.tsx',import.meta.url),'utf8');assert.doesNotMatch(source,/setInterval|setTimeout|performance\.now|Date\.now/);
 const css=await readFile(new URL('./editorial.css',import.meta.url),'utf8');assert.match(css,/@media\(prefers-reduced-motion:reduce\)\{\.analysis-spinner\{animation:none\}\}/);
});
test('workflow and unknown-state text translate without asserting the models were used',()=>{
 for(const label of analysisStageLabels)assert.notEqual(translateText(label,'zh'),label);
 const html=render(h(LanguageProvider,{value:'zh'},h(AuditProgress,{percent:null})));assert.match(html,/目前沒有各階段狀態/);assert.match(html,/可能的處理流程/);assert.match(html,/程式計算量測數字/);
});
