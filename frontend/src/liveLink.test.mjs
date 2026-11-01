import test from 'node:test';import assert from 'node:assert/strict';
import {createElement as h} from 'react';import {renderToStaticMarkup as render} from 'react-dom/server';
import {DemoUploadNotice,liveAppUrl} from '../.test-dist/DemoUploadNotice.js';import {LanguageProvider} from '../.test-dist/i18n.js';
test('static upload guidance offers a working live link in both languages, with no disabled picker',()=>{
 for(const lang of ['en','zh']){
  const html=render(h(LanguageProvider,{value:lang},h(DemoUploadNotice,{liveUrl:'https://example.hf.space/'})));
  assert.match(html,/href="https:\/\/example.hf.space\/"/);assert.match(html,/data-testid="open-live-app"/);
  assert.doesNotMatch(html,/<input|<button|disabled|git clone/);
  assert.match(html,lang==='zh'?/這個頁面只重播已存結果。/:/This page only replays saved results/);
  assert.match(html,lang==='zh'?/要上傳自己的影片，請開線上版/:/To upload your own video, open the live app/);
 }
});
test('unconfigured and invalid live URLs show the three local commands and README requirements instead',()=>{
 for(const value of ['',undefined,'not a URL','javascript:alert(1)','data:text/html,test','https://user:pass@example.com']){
  assert.equal(liveAppUrl(value),null);
  const html=render(h(DemoUploadNotice,{liveUrl:value}));
  assert.doesNotMatch(html,/data-testid="open-live-app"|<input|<button/);
  assert.match(html,/git clone https:\/\/github.com\/johncat88425-del\/slope-coach.git\ncd slope-coach\n\.\/scripts\/dev.sh/);
  assert.match(html,/href="https:\/\/github.com\/johncat88425-del\/slope-coach#installation--setup"/);
  assert.match(html,/href="#wall"/);
 }
 assert.equal(liveAppUrl(' https://example.hf.space/ '),'https://example.hf.space/');
});
