import test from 'node:test';
import assert from 'node:assert/strict';
import {renderToStaticMarkup} from 'react-dom/server';
import {CurveChart} from '../.test-dist/CurveChart.js';
const prediction={curve:[[0,0],[1,1]],prediction_id:'p'};
test('non-ok and missing observations split the observed curve rather than interpolate',()=>{
 const trial={t0_s:2,samples:[{t_s:2,s_m:0.2,quality:'ok'},{t_s:2.2,s_m:0.4,quality:'ok'},
 {t_s:2.3,s_m:0.5,quality:'position_jump'},{t_s:2.4,s_m:null,quality:'missing'},
 {t_s:2.5,s_m:0.6,quality:'ok'},{t_s:2.6,s_m:0.7,quality:'ok'}]};
 const html=renderToStaticMarkup(CurveChart({prediction,trial,comparison:{fit:{s0_m:0.2}}}));
 const orange=html.match(/<path d="([^"]*)" stroke="var\(--color-observed, #c26319\)"/)[1];
 assert.equal((orange.match(/M/g)||[]).length,2);
 assert.equal((orange.match(/L/g)||[]).length,2);
 assert.equal((html.match(/<circle /g)||[]).length,4);
 assert.match(html,/stroke-dasharray="7 5"/);
});
test('no confirmed release or fitted origin means no measured line is fabricated',()=>{
 const html=renderToStaticMarkup(CurveChart({prediction,trial:{t0_s:null,samples:[{t_s:0,s_m:0,quality:'ok'}]}}));
 assert.match(html,/<path d="" stroke="var\(--color-observed, #c26319\)"/);
 assert.equal((html.match(/<circle /g)||[]).length,0);
});
