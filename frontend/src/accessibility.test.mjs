import test from 'node:test';import assert from 'node:assert/strict';import {createElement} from 'react';import {renderToStaticMarkup} from 'react-dom/server';import {CurveChart} from '../.test-dist/CurveChart.js';
test('chart uses dash and dot shapes plus a readable data table, independently of colour',()=>{
const html=renderToStaticMarkup(createElement(CurveChart,{prediction:{curve:[[0,0],[1,2]]}}));
assert.match(html,/stroke-dasharray="7 5"/);assert.match(html,/Prediction — dashed line; observed — solid line with dots/);assert.match(html,/<summary>/);assert.match(html,/<caption>/);assert.match(html,/Time \(s\)/);assert.match(html,/tabindex="0"/);
});
