import {formatNumber} from './formatNumber.js';

export const earthRulerTitle='If this is Earth gravity at normal speed';
export const earthRulerNote='This is a reading under assumptions, not a verdict; slow motion makes the height appear larger.';
const fields=[
 ['if_earth_flight_time_s','Flight time (s)'],
 ['if_earth_vertical_extent_m','Vertical extent (m)'],
 ['if_earth_launch_speed_m_s','Initial tracked speed (m/s)'],
 ['if_earth_launch_angle_deg','Initial tracked angle (degrees)'],
] as const;
export function earthRulerReadings(numbers:Record<string,number>){
 return fields.filter(([key])=>typeof numbers[key]==='number'&&Number.isFinite(numbers[key]))
  .map(([key,label])=>({key,label,value:numbers[key],text:formatNumber(numbers[key],key)}));
}
export function earthRulerLines(numbers:Record<string,number>){
 const rows=earthRulerReadings(numbers);
 return rows.length?[earthRulerTitle,earthRulerNote,...rows.map(r=>`${r.label}: ${r.text}`)]:[];
}
