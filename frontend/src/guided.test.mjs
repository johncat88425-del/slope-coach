import test from 'node:test';import assert from 'node:assert/strict';import {demoSteps,GuidedDemo} from '../.test-dist/GuidedDemo.js';import {recordingSteps} from '../.test-dist/tourSteps.js';import {createElement} from 'react';import {renderToStaticMarkup} from 'react-dom/server';
test('both tour launch points share the final recording order and load evidence only on request',()=>{
 assert.equal(demoSteps,recordingSteps);assert.equal(demoSteps.length,6);
 assert.match(renderToStaticMarkup(createElement(GuidedDemo,{route:'home'})),/Guided demo/);
 assert.match(renderToStaticMarkup(createElement(GuidedDemo,{route:'audit',recording:true})),/Recording tour/);
});
