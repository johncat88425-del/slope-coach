import test from 'node:test';import assert from 'node:assert/strict';import {sourceLabel} from '../.test-dist/ModelSource.js';
test('model and SAM outputs are attributed to the model actually reported',()=>{assert.equal(sourceLabel('model'),'由 Muse Spark 產生');assert.equal(sourceLabel('sam'),'由 SAM 3.1 產生')});
test('mock, manual and numerical results never masquerade as model calls',()=>{for(const s of ['mock','manual','physics','frame_diff','unknown'])assert.ok(!/由 (Muse Spark|SAM)/.test(sourceLabel(s)))});
