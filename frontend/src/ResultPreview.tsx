import {useId,useState} from 'react';
import {Localize} from './i18n.js';
import {ModelSource} from './ModelSource.js';
import {formatNumber} from './formatNumber.js';
import {verdictEnglish} from './audit.js';
import type {AuditOut} from './audit.js';
export const previewVerdictLabels={consistent:'Fits the model.',inconsistent:"Doesn't fit the model.",insufficient_data:'Not enough evidence.'};
/** Preview of a stored result; every measurement comes from the selected record. */
export function ResultPreview({audit,recordKey}:{audit:AuditOut;recordKey:string}){
 const [expanded,setExpanded]=useState(false),detailsId=useId();
 const labels=previewVerdictLabels;
 const value=audit.numbers.g_apparent_m_s2;
 return <Localize><article className="result-preview" data-testid="opening-card" data-verdict={audit.verdict} data-expanded={expanded}>
 <span className="preview-status"><i aria-hidden="true"/>{labels[audit.verdict]}</span>
 <span className="preview-mark" aria-hidden="true">{audit.verdict==='consistent'?'↘':audit.verdict==='inconsistent'?'↗':'?'}</span>
 <h3><button className="preview-toggle" aria-expanded={expanded} aria-controls={detailsId} onClick={()=>setExpanded(value=>!value)}>{verdictEnglish(audit)}</button></h3><p>{audit.real_clip?'Recorded by john':'Generated test clip'}</p>
 <div id={detailsId} className="preview-evidence">{typeof value==='number'&&Number.isFinite(value)?<p className="preview-value"><span title={String(value)}>{formatNumber(value)}</span> <small>m/s²</small></p>:<p>Measurement unavailable</p>}<ModelSource source={audit.track_source} kind="tracking"/></div>
 <a className="preview-link" href={'#examples/'+encodeURIComponent(recordKey)}>Review evidence <span aria-hidden="true">↗</span></a>
 </article></Localize>;
}
