import {useId,useState} from 'react';
import type {AuditOut} from './audit.js';
import {previewVerdictLabels} from './ResultPreview.js';
import {vehicleMetrics} from './vehiclePresentation.js';
import {Localize} from './i18n.js';
export function CarPreview({records}:{records:{key:string;audit:AuditOut}[]}){
 const [expanded,setExpanded]=useState(false),detailsId=useId();
 return <Localize><article className="result-preview car-preview" data-testid="opening-card" data-category="cars" data-expanded={expanded}>
 <span className="preview-status">Synthetic test clips</span><span className="preview-mark" aria-hidden="true">↔</span>
 <h3><button className="preview-toggle" aria-expanded={expanded} aria-controls={detailsId} onClick={()=>setExpanded(value=>!value)}>Cars</button></h3><p>Explore the vehicle model.</p>
 <div id={detailsId} className="preview-evidence">{records.length?records.map(({key,audit})=>{const metrics=vehicleMetrics(audit);return <div key={key} className="car-case" data-testid="car-case" data-record-key={key}><h4><a className="car-case-link" href={'#examples/'+encodeURIComponent(key)} aria-label={metrics.accelerationLabel==='Braking'?'Review braking example':'Review acceleration example'}>{metrics.accelerationLabel} <span aria-hidden="true">↗</span></a></h4><p className="car-outcome" data-verdict={audit.verdict}>{previewVerdictLabels[audit.verdict]}</p><dl>{metrics.speed!==null&&<div><dt>Speed</dt><dd>{metrics.speed} km/h</dd></div>}{metrics.acceleration!==null&&<div><dt>Acceleration</dt><dd>{metrics.acceleration} g</dd></div>}</dl>{metrics.speed===null&&metrics.acceleration===null&&<p>Measurement unavailable</p>}</div>}):<p>The saved result is unavailable.</p>}</div>
 </article></Localize>;
}
