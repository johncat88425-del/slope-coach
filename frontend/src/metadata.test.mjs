import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
const html=await readFile(new URL('../index.html',import.meta.url),'utf8');
function meta(name){return [...html.matchAll(/<meta\s+(?:name|property)="([^"]+)"\s+content="([^"]*)"/g)].filter(match=>match[1]===name).map(match=>match[2])}
test('link previews use an absolute deployment image and matching Open Graph/Twitter text',()=>{
 for(const prefix of ['og','twitter']){assert.deepEqual(meta(prefix+':title'),['Does it fall like Earth?']);assert.equal(meta(prefix+':description').length,1);assert.doesNotMatch(meta(prefix+':description')[0],/detects AI|fake detector|any video/i);assert.deepEqual(meta(prefix+':image'),['https://johncat88425-del.github.io/slope-coach/og.png']);assert.ok(meta(prefix+':image:alt')[0]);}
 assert.deepEqual(meta('twitter:card'),['summary_large_image']);assert.deepEqual(meta('og:image:width'),['1200']);assert.deepEqual(meta('og:image:height'),['630']);assert.deepEqual(meta('og:image:type'),['image/png']);
 assert.ok(html.includes('href="/favicon.svg"'));assert.ok(html.includes('href="/favicon.ico"'));
});
test('committed preview and favicon assets have valid dimensions and the specified motion mark',async()=>{
 const png=await readFile(new URL('../public/og.png',import.meta.url));assert.deepEqual([...png.subarray(0,8)],[137,80,78,71,13,10,26,10]);assert.equal(png.readUInt32BE(16),1200);assert.equal(png.readUInt32BE(20),630);assert.ok(png.length<300000);
 const svg=await readFile(new URL('../public/favicon.svg',import.meta.url),'utf8');assert.match(svg,/stroke-dasharray=/);assert.match(svg,/<circle[^>]*fill="#f5a524"/);
 const ico=await readFile(new URL('../public/favicon.ico',import.meta.url));assert.equal(ico.readUInt16LE(2),1);assert.ok(ico.readUInt16LE(4)>0);
});
