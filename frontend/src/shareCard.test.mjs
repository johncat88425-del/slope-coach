import test from 'node:test';
import assert from 'node:assert/strict';
import {shareCardContent,shareCardSize} from '../.test-dist/cardExport.js';
const base={audit_id:'share',verdict:'inconsistent',assumed_model:'free_flight',track_source:'sam',numbers:{g_vs_earth:.014565344180615633,g_apparent_m_s2:.14288602641183937}};
test('share card formats the supplied ratio, falls back to supplied SI values and never derives a ratio',()=>{
 const before=JSON.stringify(base),card=shareCardContent(base);assert.equal(card.value,'0.0146×');assert.equal(card.caption,"of Earth's gravity.");assert.equal(card.background,'#f5a524');assert.equal(card.tracking,'Tracked by SAM 3.1');assert.equal(JSON.stringify(base),before);
 const fallback=shareCardContent({...base,numbers:{g_apparent_m_s2:.142886}});assert.equal(fallback.value,'0.143');assert.equal(fallback.unit,'m/s²');assert.doesNotMatch(fallback.value,/×|\//);
 assert.equal(shareCardContent({...base,numbers:{}}).value,'—');
});
test('every outcome has text, its own palette and honest source/provenance labels',()=>{
 assert.deepEqual(shareCardSize,{width:1080,height:1920});
 for(const [verdict,background] of Object.entries({consistent:'#5ab0f0',inconsistent:'#f5a524',insufficient_data:'#b7bcc5'})){
  const card=shareCardContent({...base,verdict,track_source:'frame_diff',synthetic:true});assert.equal(card.background,background);assert.ok(card.verdict);assert.match(card.tracking,/no model/);assert.match(card.provenance,/Program simulation/);assert.doesNotMatch(card.tracking,/SAM/);
  if(verdict==='insufficient_data')assert.equal(card.value,'—');assert.match(card.footer,/Checks motion against a model/);
 }
});
