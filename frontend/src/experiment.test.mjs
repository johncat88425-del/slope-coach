import test from 'node:test';
import assert from 'node:assert/strict';
import {createExperiment, imagePoint, pages, replacePhoto, resolveRoute, saveCalibration, updateDraft, validateDraft} from '../.test-dist/experiment.js';
function validExperiment() {
  const e = createExperiment('test');
  e.draft = {...e.draft, photo: {name: 'slope.png', url: 'blob:test'}, size: {width: 1000, height: 500}, points: [{x:0,y:0},{x:500,y:0},{x:100,y:100},{x:1000,y:0}], length:'1', height:'0.2', rulerLength:'0.3', captureConfirmed:true};
  return e;
}
test('all five routes resolve; unknown and empty routes return setup', () => {
  assert.equal(pages.length, 5);
  for (const {route} of pages) assert.equal(resolveRoute('#' + route), route);
  assert.equal(resolveRoute('#unknown'), 'setup');
  assert.equal(resolveRoute(''), 'setup');
});
test('saves a valid user-confirmed snapshot without mutating the draft', () => {
  const e = validExperiment(); const saved = saveCalibration(e);
  assert.deepEqual(validateDraft(e.draft), []);
  assert.equal(saved.calibration.lengthM, 1);
  assert.equal(saved.calibration.source, 'user_confirmed');
  e.draft.points[0].x = 10;
  assert.equal(saved.calibration.points[0].x, 0);
  assert.equal(e.calibration, null);
});
test('blocks missing, zero, negative, nonfinite and impossible dimensions for every field', () => {
  for (const key of ['length','height','rulerLength']) {
    for (const value of ['', ' ', '0', '-1', 'Infinity', 'NaN']) {
      const e = validExperiment(); e.draft[key] = value;
      assert.ok(validateDraft(e.draft).length, `${key}=${value}`);
      assert.equal(saveCalibration(e).calibration, null);
    }
  }
  for (const value of ['1','1.1']) {
    const e = validExperiment(); e.draft.height = value;
    assert.ok(validateDraft(e.draft).some(s => s.includes('h ≥ L')));
  }
});
test('requires loaded media, four valid points and confirmed capture conditions', () => {
  for (const patch of [{photo:null},{size:{width:0,height:0}},{points:[]},{captureConfirmed:false},
    {points:[{x:0,y:0},{x:0,y:0},{x:10,y:10}]},
    {points:[{x:0,y:0},{x:500,y:0},{x:1001,y:10}]},
    {points:[{x:0,y:0},{x:500,y:0},{x:NaN,y:10}]}]) {
    const e = validExperiment(); Object.assign(e.draft,patch);
    assert.ok(validateDraft(e.draft).length); assert.equal(saveCalibration(e).calibration,null);
  }
});
test('responsive photo clicks map to original pixels; outside and unloaded clicks are rejected', () => {
  const rect = {left:20,top:40,width:500,height:250}; const size = {width:1000,height:500};
  assert.deepEqual(imagePoint({x:270,y:165},rect,size),{x:500,y:250});
  assert.equal(imagePoint({x:19,y:100},rect,size),null);
  assert.equal(imagePoint({x:521,y:100},rect,size),null);
  assert.equal(imagePoint({x:270,y:165},{...rect,width:0},size),null);
});
test('editing invalidates saved calibration; replacing media clears stale points and confirmation', () => {
  const saved = saveCalibration(validExperiment());
  const changed = updateDraft(saved,{height:'0.3'});
  assert.equal(changed.calibration,null); assert.equal(saved.calibration.heightM,0.2);
  const replaced = replacePhoto(saved,{name:'new.jpg',url:'blob:new'});
  assert.deepEqual(replaced.draft.points,[]); assert.equal(replaced.draft.captureConfirmed,false);
  assert.equal(replaced.draft.size.width,0); assert.equal(replaced.calibration,null);
  assert.equal(replaced.id,saved.id);
});
