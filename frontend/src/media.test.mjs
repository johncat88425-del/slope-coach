import test from 'node:test';
import assert from 'node:assert/strict';
import {mediaUrl} from '../.test-dist/media.js';
test('backend photos and videos use same-origin media proxy by default',()=>{
 assert.equal(mediaUrl('/media/exp/photo.jpg'),'/media/exp/photo.jpg');
 assert.equal(mediaUrl(null),undefined);assert.equal(mediaUrl(''),undefined);
});
test('explicit API origin resolves media on that backend, not frontend',()=>{
 assert.equal(mediaUrl('/media/e/v.mp4','http://localhost:8000/'),'http://localhost:8000/media/e/v.mp4');
});
test('untrusted paths and non-http backend URLs are not used for media',()=>{
 for(const p of ['javascript:alert(1)','https://third.party/image','//third.party/media/a','/api/a'])assert.equal(mediaUrl(p),undefined);
 assert.equal(mediaUrl('/media/a','file:///tmp'),undefined);
});
