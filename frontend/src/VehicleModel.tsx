import {vehicleClassReferences,vehicleMetrics} from './vehiclePresentation.js';
import type {VehicleClass} from './vehiclePresentation.js';
import {useId} from 'react';
import type {AuditOut} from './audit.js';
import {formatNumber} from './formatNumber.js';
import {Localize} from './i18n.js';

export function AuditDimensionField({model,value,onChange}:{model:string;value:string;onChange:(value:string)=>void}){
 const hintId=useId(),vehicle=model==='vehicle';
 return <Localize>
  <label>{vehicle?'Car body length (metres)':'Measured object size (metres, optional)'}
   <input type="number" min="0" step="any" value={value} aria-describedby={hintId} onChange={e=>onChange(e.target.value)}/>
  </label>
  <p id={hintId}>{vehicle?'A typical sedan is about 4.5 m long, an SUV about 4.8 m, and a small car about 3.5 m; check the manufacturer’s specification if you know the model. You can leave this blank: the backend checks both 3 m and 6 m and gives a verdict only when they agree.':'Enter a user-confirmed measurement. Leave unknown dimensions blank; do not infer them from the object name.'}</p>
  {vehicle&&<p data-testid="vehicle-window-hint">Select the seconds when the whole car is visible and drives from left to right.</p>}
 </Localize>;
}

/** The selected class is sent to the backend; no midpoint or measured length is filled here. */
export function VehicleClassField({value,onChange}:{value:VehicleClass|'';onChange:(value:VehicleClass|'')=>void}){
 const hintId=useId(),reference=vehicleClassReferences.find(row=>row.value===value);
 return <Localize><div className="vehicle-class-field"><label>What kind of car is this?<select data-testid="vehicle-class" aria-describedby={hintId} value={value} onChange={event=>onChange(event.target.value as VehicleClass|'')}><option value="">Choose…</option>{vehicleClassReferences.map(row=><option key={row.value} value={row.value}>{row.label}</option>)}</select></label>
 <p id={hintId}>{reference&&<><span>API reference length range (m): </span><strong>{reference.range}</strong><br/></>}<span>Confirm this reference range, or enter a measured car length below to override it. The reference is not a user measurement.</span></p></div></Localize>;
}
/** Display backend measurements only. Formatting never changes stored data or the verdict. */
export function VehicleMeasurements({audit}:{audit:AuditOut}){
 if(audit.assumed_model!=='vehicle')return null;
 const n=audit.numbers,has=(key:string)=>typeof n[key]==='number'&&Number.isFinite(n[key]);
 const metrics=vehicleMetrics(audit),{knownLength,accelerationLabel}=metrics;
 return <Localize><section className="vehicle-measurements" data-verdict={audit.verdict} data-testid="vehicle-measurements" aria-label="Vehicle measurements">
  {audit.synthetic&&<p className="source-label" data-testid="vehicle-synthetic">Program simulation — program-drawn moving squares.</p>}
  <h3>Vehicle measurements</h3>
  <p>{knownLength?'Scale: user-confirmed car body length.':metrics.lengthRange?<><span>Estimated using a car length of </span><strong>{metrics.lengthRange}</strong><span> m.</span></>:'Scale: no car length provided; speed is shown in car body lengths only.'}</p>
  <dl className="vehicle-statistics">
   {metrics.speed&&<div data-testid={knownLength?'vehicle-speed':'vehicle-speed-range'}><dt>{knownLength?'Speed':'Estimated speed range'}</dt><dd title={knownLength?String(n.speed_km_h):`${n.speed_km_h_low}–${n.speed_km_h_high}`}>{metrics.speed} km/h</dd></div>}
   {metrics.acceleration&&<div data-testid={knownLength?'vehicle-acceleration':'vehicle-acceleration-range'}><dt>{accelerationLabel}{!knownLength&&<span> · Estimated range</span>}</dt><dd title={knownLength?String(n.accel_g):`${n.accel_g_low}–${n.accel_g_high}`}>{metrics.acceleration} g</dd><p className="grip-limit">Grip limit: 1.2 g</p></div>}
   {has('speed_car_lengths_s')&&<div data-testid="vehicle-length-speed"><dt>Car body lengths per second</dt><dd title={String(n.speed_car_lengths_s)}>{formatNumber(n.speed_car_lengths_s)}</dd></div>}
  </dl>
  {has('car_length_for_max_accel_m')&&<p data-testid="vehicle-required-length"><span>This car would need to be </span><span title={String(n.car_length_for_max_accel_m)}>{formatNumber(n.car_length_for_max_accel_m,'car_length_for_max_accel_m')}</span><span> metres long for this acceleration to be exactly 1.2 g.</span></p>}
  <p>Typical car tyres support about 1 g of grip; above 1.2 g is inconsistent with the assumption of a car driving on a road. This does not determine video authenticity.</p>
 </section></Localize>;
}
