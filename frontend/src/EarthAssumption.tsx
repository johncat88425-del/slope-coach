import {Localize} from './i18n.js';
import {earthRulerReadings,earthRulerTitle,earthRulerNote,earthConditionPrefix} from './earthRuler.js';

export function EarthAssumption({numbers}:{numbers:Record<string,number>}){
 const rows=earthRulerReadings(numbers);if(!rows.length)return null;
 return <Localize><section data-testid="earth-assumption" aria-label={earthRulerTitle}>
  <h3>{earthRulerTitle}</h3><p>{earthRulerNote}</p>
  <dl>{rows.map(r=><div key={r.key} data-testid={r.key}><dt><span>{earthConditionPrefix}</span> {r.label}</dt><dd title={String(r.value)}>{r.text}</dd></div>)}</dl>
 </section></Localize>;
}
