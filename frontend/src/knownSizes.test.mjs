import test from 'node:test';
import assert from 'node:assert/strict';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {knownSize} from '../.test-dist/knownSizes.js';
import {AuditDimensionField} from '../.test-dist/VehicleModel.js';

test('T254: common balls get a fixed official size; other names get none',()=>{
 assert.equal(knownSize('orange basketball')?.metres,0.24);
 assert.equal(knownSize('Tennis ball')?.metres,0.067);
 assert.equal(knownSize('brown paper ball'),null);
 assert.equal(knownSize('ball'),null);
});
test('T254: the size field offers the standard size as a button only while empty and not for cars',()=>{
 const f=()=>{};
 assert.match(renderToStaticMarkup(createElement(AuditDimensionField,{model:'free_flight',value:'',onChange:f,objectName:'basketball'})),/use-standard-size.*0\.24 m/);
 assert.doesNotMatch(renderToStaticMarkup(createElement(AuditDimensionField,{model:'free_flight',value:'0.2',onChange:f,objectName:'basketball'})),/use-standard-size/);
 assert.doesNotMatch(renderToStaticMarkup(createElement(AuditDimensionField,{model:'vehicle',value:'',onChange:f,objectName:'basketball'})),/use-standard-size/);
});
