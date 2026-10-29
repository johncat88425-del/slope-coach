import {LanguageProvider} from '../.test-dist/i18n.js';
import {createElement} from 'react';
import test from 'node:test';import assert from 'node:assert/strict';
import {renderToStaticMarkup as rawRender} from 'react-dom/server';
import {Trajectory2D,TrajectoryOverlay} from '../.test-dist/Trajectory.js';
test('raw audit points stay scatter-only when frame quality is absent',()=>{const h=render(Trajectory2D({points:[{t:0,x:1,y:2},{t:10,x:3,y:4}]}));assert.equal((h.match(/<circle/g)||[]).length,2);assert.ok(!h.includes('<path'));assert.match(h,/480 px/)});
test('explicit missing or unreliable points break connected paths',()=>{const h=render(Trajectory2D({connect:true,points:[{t:0,x:1,y:2},{t:1,x:null,y:null},{t:2,x:3,y:4},{t:3,x:4,y:5,quality:'position_jump'},{t:4,x:6,y:7}]}));const d=h.match(/<path d="([^"]*)"/)[1];assert.equal((d.match(/M/g)||[]).length,3);assert.equal((h.match(/<circle/g)||[]).length,3)});
test('empty tracks and missing overlay are explicit, supplied overlay is used unchanged',()=>{assert.match(render(Trajectory2D({points:[]})),/尚無/);assert.match(render(TrajectoryOverlay({})),/無可用/);assert.match(render(TrajectoryOverlay({url:'/media/a/overlay.png'})),/src="\/media\/a\/overlay.png"/)});

function render(node){return rawRender(createElement(LanguageProvider,{value:'zh'},node))}
