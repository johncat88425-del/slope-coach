import type {AuditOut} from './audit.js';
export type VehicleClass='compact_car'|'sedan'|'suv'|'pickup'|'unknown';
/** Display strings copied from docs/API.md v1.2 / T190; never used to calculate measurements. */
export const vehicleClassReferences=[
 {value:'compact_car',label:'Compact car',range:'4.3–4.75'},
 {value:'sedan',label:'Sedan',range:'4.6–5.0'},
 {value:'suv',label:'SUV',range:'4.5–4.85'},
 {value:'pickup',label:'Pickup',range:'5.3–5.95'},
 {value:'unknown',label:'Unknown',range:'3–6'},
] as const;
export function vehicleMetrics(a:AuditOut){
 const n=a.numbers,has=(key:string)=>typeof n[key]==='number'&&Number.isFinite(n[key]);
 const knownLength=typeof a.object_size_m==='number'&&Number.isFinite(a.object_size_m)&&a.object_size_m>0;
 const range=(low:string,high:string,digits:number)=>has(low)&&has(high)?`${n[low].toFixed(digits)}–${n[high].toFixed(digits)}`:null;
 const lengthRange=has('car_length_low_m')&&has('car_length_high_m')?`${n.car_length_low_m}–${n.car_length_high_m}`:null;
 return {knownLength,lengthRange,
  speed:knownLength?(has('speed_km_h')?n.speed_km_h.toFixed(0):null):range('speed_km_h_low','speed_km_h_high',0),
  acceleration:knownLength?(has('accel_g')?n.accel_g.toFixed(2):null):range('accel_g_low','accel_g_high',2),
  accelerationLabel:has('accel_m_s2')?(n.accel_m_s2<0?'Braking':n.accel_m_s2>0?'Acceleration':'Acceleration / braking'):'Acceleration / braking'};
}
