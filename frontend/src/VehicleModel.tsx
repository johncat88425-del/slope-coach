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

/** Display backend measurements only. Formatting never changes stored data or the verdict. */
export function VehicleMeasurements({audit}:{audit:AuditOut}){
 if(audit.assumed_model!=='vehicle')return null;
 const n=audit.numbers,has=(key:string)=>typeof n[key]==='number'&&Number.isFinite(n[key]);
 const knownLength=typeof audit.object_size_m==='number'&&Number.isFinite(audit.object_size_m)&&audit.object_size_m>0;
 const accelerationLabel=has('accel_m_s2')?(n.accel_m_s2<0?'Braking':n.accel_m_s2>0?'Acceleration':'Acceleration / braking'):'Acceleration / braking';
 return <Localize><section className="vehicle-measurements" data-testid="vehicle-measurements" aria-label="Vehicle measurements">
  {audit.synthetic&&<p className="source-label" data-testid="vehicle-synthetic">Program simulation — program-drawn moving squares.</p>}
  <h3>Vehicle measurements</h3>
  <p>{knownLength?'Scale: user-confirmed car body length.':'Scale: no car length provided; speed is shown in car body lengths only.'}</p>
  <dl>
   {knownLength&&has('speed_km_h')&&<div data-testid="vehicle-speed"><dt>Speed</dt><dd title={String(n.speed_km_h)}>{n.speed_km_h.toFixed(0)} km/h</dd></div>}
   {knownLength&&has('accel_g')&&<div data-testid="vehicle-acceleration"><dt>{accelerationLabel}</dt><dd title={String(n.accel_g)}>{n.accel_g.toFixed(2)} g</dd></div>}
   {has('speed_car_lengths_s')&&<div data-testid="vehicle-length-speed"><dt>Car body lengths per second</dt><dd title={String(n.speed_car_lengths_s)}>{formatNumber(n.speed_car_lengths_s)}</dd></div>}
  </dl>
  {has('car_length_for_max_accel_m')&&<p data-testid="vehicle-required-length"><span>This car would need to be </span><span title={String(n.car_length_for_max_accel_m)}>{formatNumber(n.car_length_for_max_accel_m,'car_length_for_max_accel_m')}</span><span> metres long for this acceleration to be exactly 1.2 g.</span></p>}
  <p>Typical car tyres support about 1 g of grip; above 1.2 g is inconsistent with the assumption of a car driving on a road. This does not determine video authenticity.</p>
 </section></Localize>;
}
