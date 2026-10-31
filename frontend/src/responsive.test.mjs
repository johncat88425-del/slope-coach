import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {ResultPreview} from '../.test-dist/ResultPreview.js';
const css=await readFile(new URL('./editorial.css',import.meta.url),'utf8');
test('390px layout contract keeps every primary region shrinkable without clipping the page',()=>{
 // Geometry is additionally checked in the browser at 390 and 768; Node has no layout engine.
 for(const rule of ['grid-template-columns:minmax(0,1fr)','min-width:0','max-width:390px','min-height:44px','font-size:clamp(44px,6.5vw,52px)'])assert.ok(css.includes(rule),rule);
 assert.match(css,/@media\(max-width:800px\)[\s\S]*?\.opening-cards\{grid-template-columns:minmax\(0,1fr\)\}/);
 assert.match(css,/\.process-steps\{flex-direction:column\}/);
 assert.doesNotMatch(css,/(?:html|body|main)[^}]*overflow-x\s*:\s*(hidden|clip)/);
 assert.match(css,/@media\(hover:hover\) and \(min-width:801px\)/);
});
test('each result has a separate accessible disclosure and evidence link for touch',async()=>{
 const audit=JSON.parse(await readFile(new URL('../../data/demo/generated_meta_clip4.json',import.meta.url),'utf8'));
 const html=render(h(ResultPreview,{audit,recordKey:'example'}));
 assert.match(html,/<button[^>]*aria-expanded="false"[^>]*aria-controls="[^"]+"/);
 assert.match(html,/data-expanded="false"/);assert.match(html,/<a[^>]*href="#examples\/example"/);
});
