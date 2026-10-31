import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
import {translateText} from '../.test-dist/i18n.js';
import {shareCardContent} from '../.test-dist/cardExport.js';
import {vehicleClassReferences} from '../.test-dist/vehiclePresentation.js';
const files=['Home','HomeMotion','ResultPreview','OpeningCards','ResultsWall','HowItWorks','SiteHeader','PhysicsCard','MuseAuditOutputs','RetakeGuide','VehicleModel','InterviewPanel'];
const units=new Set(['km/h','m/s²']);
const prohibited=/fake[ -]+detector|detect(?:s|ing)?\s+AI|real\s+or\s+fake|\bproves\b|\bany video\b|偵測\s*AI|假影片|真假/i;
test('every new v4 static label and accessible name has a Chinese translation',async()=>{
 const missing=[];
 for(const name of files){
  const text=await readFile(new URL(name+'.tsx',import.meta.url),'utf8'),source=ts.createSourceFile(name,text,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
  function check(text){text=text.replace(/\s+/g,' ').trim();if(/[A-Za-z]{2}/.test(text)&&!units.has(text)&&translateText(text,'zh')===text)missing.push(name+': '+text)}
  function walk(node){if(ts.isJsxText(node))check(node.text);if(ts.isJsxAttribute(node)&&['aria-label','alt','title','placeholder'].includes(node.name.text)&&node.initializer&&ts.isStringLiteral(node.initializer))check(node.initializer.text);ts.forEachChild(node,walk)}walk(source);
 }
 for(const text of vehicleClassReferences.map(row=>row.label))if(translateText(text,'zh')===text)missing.push(text);
 for(const assumed_model of ['free_flight','pendulum','vehicle'])for(const verdict of ['consistent','inconsistent','insufficient_data'])for(const track_source of ['sam','manual','color','frame_diff']){
  const card=shareCardContent({assumed_model,verdict,track_source,numbers:{g_vs_earth:.5,period_s:1,speed_km_h:50,accel_g:.5},object_size_m:4.5,synthetic:true});
  for(const key of ['caption','tracking','numbers','footer','provenance'])if(card[key]&&translateText(card[key],'zh')===card[key])missing.push('share card '+key+': '+card[key]);
 }
 assert.deepEqual([...new Set(missing)],[]);
});
test('new pages and generated share copy avoid prohibited claims',async()=>{
 for(const name of [...files,'cardExport','vehiclePresentation'])assert.doesNotMatch(await readFile(new URL(name+(name==='cardExport'||name==='vehiclePresentation'?'.ts':'.tsx'),import.meta.url),'utf8'),prohibited,name);
 for(const verdict of ['consistent','inconsistent','insufficient_data']){
  const card=shareCardContent({assumed_model:'free_flight',verdict,track_source:'sam',numbers:{}});
  assert.doesNotMatch(Object.values(card).filter(x=>typeof x==='string').join(' '),prohibited);
 }
});
