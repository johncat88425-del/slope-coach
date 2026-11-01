import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {createElement} from 'react';import {renderToStaticMarkup} from 'react-dom/server';import {HomeMotion} from '../.test-dist/HomeMotion.js';
test('the home hero reserves its real aspect ratio and requests the smaller WebP at high priority',async()=>{
 const html=renderToStaticMarkup(createElement(HomeMotion,{}));
 assert.match(html,/<img[^>]*src="\/images\/motion-study\.webp"/);
 assert.match(html,/width="1280" height="720"/);assert.match(html,/fetchPriority="high"/i);assert.doesNotMatch(html,/loading="lazy"/);
 const [webp,jpeg]=await Promise.all(['webp','jpg'].map(ext=>readFile(new URL('../public/images/motion-study.'+ext,import.meta.url))));
 assert.equal(webp.toString('ascii',0,4),'RIFF');assert.equal(webp.toString('ascii',8,12),'WEBP');assert.ok(webp.length<jpeg.length);
 const entry=await readFile(new URL('../index.html',import.meta.url),'utf8');
 assert.match(entry,/<link rel="preload" as="image" href="\/images\/motion-study\.webp" fetchpriority="high"\/>/);
});
