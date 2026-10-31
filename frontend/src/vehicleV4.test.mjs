import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createElement as h} from 'react';
import {renderToStaticMarkup as render} from 'react-dom/server';
import {VehicleMeasurements,VehicleClassField} from '../.test-dist/VehicleModel.js';
import {vehicleMetrics,vehicleClassReferences} from '../.test-dist/vehiclePresentation.js';
import {shareCardContent} from '../.test-dist/cardExport.js';
import {LanguageProvider} from '../.test-dist/i18n.js';
import {createApi} from '../.test-dist/api.js';
const car=JSON.parse(await readFile(new URL('../../data/demo/synthetic_car_50kmh_braking.json',import.meta.url),'utf8'));
test('vehicle reference ranges match the published API and never populate measured length',async()=>{
 const apiDoc=await readFile(new URL('../../docs/API.md',import.meta.url),'utf8');
 for(const row of vehicleClassReferences){assert.ok(apiDoc.includes('`'+row.value+'`'));assert.ok(apiDoc.includes(row.range+' m'));}
 const html=render(h(LanguageProvider,{value:'zh'},h(VehicleClassField,{value:'sedan',onChange(){throw Error('must not fill a measurement')}})));
 assert.match(html,/這是什麼車/);assert.match(html,/4.6–5.0/);assert.match(html,/不是使用者量測值/);assert.doesNotMatch(html,/<input/);
});
test('vehicle results and share cards display only backend speed and acceleration, including range estimates',()=>{
 const a={...car,object_size_m:null,numbers:{car_length_low_m:3,car_length_high_m:6,speed_km_h_low:41.4,speed_km_h_high:82.9,accel_g_low:.234,accel_g_high:.567,speed_km_h:9999,accel_g:9999}},before=JSON.stringify(a);
 const metrics=vehicleMetrics(a);assert.equal(metrics.speed,'41–83');assert.equal(metrics.acceleration,'0.23–0.57');assert.equal(metrics.lengthRange,'3–6');
 const html=render(h(LanguageProvider,{value:'zh'},h(VehicleMeasurements,{audit:a})));assert.match(html,/3–6/);assert.match(html,/車長估計/);assert.match(html,/41–83 km\/h/);assert.match(html,/0.23–0.57 g/);assert.match(html,/上限 1.2 g/);assert.doesNotMatch(html,/9999/);
 const card=shareCardContent(a);assert.equal(card.value,'41–83');assert.equal(card.unit,'km/h');assert.equal(card.reference,'3–6');assert.equal(card.secondary.value,'0.23–0.57');assert.equal(JSON.stringify(a),before);
 assert.equal(vehicleMetrics({...a,numbers:{speed_km_h:99}}).speed,null);
 const known=shareCardContent({...car,numbers:{speed_km_h:72.4,accel_g:.6543,accel_m_s2:-1000}});assert.equal(known.value,'72');assert.equal(known.secondary.value,'0.65');assert.equal(known.secondary.label,'Braking');
 const onlyAcceleration=shareCardContent({...car,numbers:{accel_g:.5}});assert.equal(onlyAcceleration.unit,'g');assert.equal(onlyAcceleration.value,'0.50');assert.equal(onlyAcceleration.limit,'Grip limit: 1.2 g');
});
test('both upload paths send the confirmed class with optional user measurement untouched',async()=>{
 const bodies=[],api=createApi('',async(url,init)=>{bodies.push(init.body);return Response.json(car)});
 await api.auditFromDraft('car',{t_start:1,t_end:2,camera_static:true,assumed_model:'vehicle',vehicle_class:'sedan'});
 await api.audit(new File(['fixture'],'car.mp4'),1,2,true,4.512345,'vehicle',undefined,undefined,'car',false,'pickup');
 assert.equal(bodies[0].get('vehicle_class'),'sedan');assert.equal(bodies[0].has('object_size_m'),false);assert.equal(bodies[1].get('vehicle_class'),'pickup');assert.equal(bodies[1].get('object_size_m'),'4.512345');
});
