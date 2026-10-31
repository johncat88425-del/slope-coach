import {Localize} from './i18n.js';
import {ModelSource} from './ModelSource.js';
import {formatNumber} from './formatNumber.js';
import {verdictEnglish} from './audit.js';
import type {AuditOut} from './audit.js';
/** Preview of a stored result; every measurement comes from the selected record. */
export function ResultPreview({audit,recordKey}:{audit:AuditOut;recordKey:string}){
 const labels={consistent:'Fits the model.',inconsistent:"Doesn't fit the model.",insufficient_data:'Not enough evidence.'};
 const value=audit.numbers.g_apparent_m_s2;
 return <Localize><a className="result-preview" data-testid="opening-card" data-verdict={audit.verdict} href={'#examples/'+encodeURIComponent(recordKey)}>
 <span className="preview-status"><i aria-hidden="true"/>{labels[audit.verdict]}</span>
 <span className="preview-mark" aria-hidden="true">{audit.verdict==='consistent'?'↘':audit.verdict==='inconsistent'?'↗':'?'}</span>
 <h3>{verdictEnglish(audit)}</h3><p>{audit.real_clip?'Recorded by john':'Generated test clip'}</p>
 <div className="preview-evidence">{typeof value==='number'&&Number.isFinite(value)?<p className="preview-value"><span title={String(value)}>{formatNumber(value)}</span> <small>m/s²</small></p>:<p>Measurement unavailable</p>}<ModelSource source={audit.track_source} kind="tracking"/></div>
 <span className="preview-link">Review evidence <span aria-hidden="true">↗</span></span>
 </a></Localize>;
}
