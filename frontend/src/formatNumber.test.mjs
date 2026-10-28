import test from 'node:test';import assert from 'node:assert/strict';import {formatNumber} from '../.test-dist/formatNumber.js';
test('display formatting rounds text only and retains small nonzero values',()=>{const a={g_vs_earth:.264321,implied_object_size_m:2.4321};assert.equal(formatNumber(a.g_vs_earth,'g_vs_earth'),'0.26');assert.equal(formatNumber(a.implied_object_size_m,'implied_object_size_m'),'2.43');assert.equal(a.g_vs_earth,.264321);assert.equal(formatNumber(.00000042),'4.20e-7');assert.equal(formatNumber(NaN),'—');assert.equal(formatNumber(-0),'0')});

test("dimensions retain three significant figures",()=>{for(const [v,expected] of [[.067,"0.0670"],[2.4,"2.40"],[.25,"0.250"],[.000067,"0.0000670"]])assert.equal(formatNumber(v,"object_size_m"),expected)});
