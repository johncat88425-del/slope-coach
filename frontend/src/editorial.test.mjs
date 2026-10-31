import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {AuditSteps} from '../.test-dist/AuditSteps.js';
import {AuditPage} from '../.test-dist/AuditPage.js';
import {SiteHeader,SiteFooter} from '../.test-dist/SiteHeader.js';
import {LanguageProvider} from '../.test-dist/i18n.js';
import {createApi} from '../.test-dist/api.js';
const api=createApi('',async()=>{throw Error('rendering must not submit a request')});
test('workflow guide reports one current step and works in both languages',()=>{
 for(const current of [0,1,2,3]){
  const html=render(h(AuditSteps,{current}));assert.equal((html.match(/aria-current="step"/g)||[]).length,1);assert.equal((html.match(/<li/g)||[]).length,4);assert.doesNotMatch(html,/%|progressbar/);
 }
 const zh=render(h(LanguageProvider,{value:'zh'},h(AuditSteps,{current:1})));for(const word of ['上傳','確認','檢查','結果'])assert.ok(zh.includes(word));
});
test('the primary entry exposes the upload before the saved image and keeps advanced tools collapsed',()=>{
 const html=render(h(AuditPage,{api}));assert.match(html,/<h1>Check the physics in your video\.<\/h1>/);assert.ok(html.indexOf('data-testid="interview-video"')<html.indexOf('<img'));assert.match(html,/data-testid="interview-prepare" hidden="" disabled=""/);assert.match(html,/aria-label="Interview video"/);
 for(const id of ['advanced-audit','offline-import'])assert.doesNotMatch(html.match(new RegExp('<details[^>]*data-testid="'+id+'"[^>]*>'))[0],/\bopen/);
 assert.match(html,/A frame from one of our Meta AI test clips/);assert.doesNotMatch(html,/\b(?:fake|detect AI)\b/i);
});
test('navigation preserves existing destinations and marks the active route',()=>{
 const html=render(h(SiteHeader,{api,route:'wall'}))+render(h(SiteFooter,{api,route:'wall'}));for(const route of ['audit','wall','compare','how','home','demo','setup'])assert.ok(html.includes('href="#'+route+'"'));
 assert.equal((html.match(/aria-current="page"/g)||[]).length,1);assert.match(html,/data-testid="nav-wall" href="#wall" aria-current="page"/);assert.match(html,/Skip to workspace/);
});
test('editorial layout keeps readable controls, responsive columns, reduced motion and a local licensed font',async()=>{
 const css=await readFile(new URL('./editorial.css',import.meta.url),'utf8');assert.match(css,/font-display:swap/);assert.match(css,/min-height:48px/);assert.match(css,/\.video-picker:focus-within/);assert.match(css,/@media\(max-width:800px\)/);assert.match(css,/@media\(max-width:480px\)/);assert.match(css,/@media\(prefers-reduced-motion:reduce\)/);assert.match(css,/\[hidden\]\s*\{\s*display:none!important;?\s*\}/);assert.doesNotMatch(css,/body[^}]*overflow-x\s*:\s*hidden/);
 const license=await readFile(new URL('./assets/NotoSansTC-OFL.txt',import.meta.url),'utf8');assert.match(license,/SIL OPEN FONT LICENSE/);
});
