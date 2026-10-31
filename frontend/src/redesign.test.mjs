import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {Home} from '../.test-dist/Home.js';
import {ResultPreview} from '../.test-dist/ResultPreview.js';
import {LanguageProvider} from '../.test-dist/i18n.js';
const audit=JSON.parse(await readFile(new URL('../../data/demo/generated_meta_clip4.json',import.meta.url),'utf8'));
test('home uses stored trajectories without measurements or new calculations',()=>{
 const before=JSON.stringify(audit),html=render(h(Home,{example:audit}));
 assert.match(html,/Does it fall like/);assert.match(html,/Earth\?/);assert.match(html,/hero-earth/);assert.match(html,/hero-observed/);
 assert.match(html,/Generated test clip/);assert.doesNotMatch(html,/m\/s|0\.143|28\.7/);assert.equal(JSON.stringify(audit),before);
});
test('preview displays only saved evidence, omits missing measurements and translates owned labels',()=>{
 const html=render(h(ResultPreview,{audit,recordKey:'generated_meta_clip4'}));assert.match(html,/0\.143/);assert.match(html,/Tracked by SAM 3.1/);assert.match(html,/#examples\/generated_meta_clip4/);
 const missing=render(h(ResultPreview,{audit:{...audit,numbers:{}},recordKey:'missing'}));assert.match(missing,/Measurement unavailable/);assert.doesNotMatch(missing,/NaN|undefined/);
 const zh=render(h(LanguageProvider,{value:'zh'},h(Home,{example:audit})));assert.match(zh,/地球重力嗎/);assert.match(zh,/檢查影片/);
});
