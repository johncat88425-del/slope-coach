import {Verbatim} from './ModelHeadline.js';
import {verdictEnglish} from './audit';
import {demoRecords} from './DemoCatalog';
import {AuditResult} from './AuditPage';
import {ModelSource} from './ModelSource';
import {Localize} from './i18n';
export function ResultsWall(){return <Localize><section data-testid="results-wall"><h2>Every clip, the same rules</h2><p>Each clip is checked with the same rules; results describe only consistency with the assumed motion model.</p><div className="results-grid">{demoRecords.map(({key,audit:a},i)=><article key={key} data-testid="wall-card"><h3>Saved clip {i+1}</h3><p>{a.real_clip?'Recorded by john; annotations confirmed by john.':'Generated test clip'}</p><p>{verdictEnglish(a)}</p><p>{a.explanation?<Verbatim text={a.explanation.text}/>:'No explanation was supplied.'}</p><p>Nearest gravity analogy: {a.nearest_body??'Not available'}</p><ModelSource source={a.track_source} kind="tracking"/>{a.verdict==='insufficient_data'&&<ul>{a.reasons.map((r,i)=><li key={i}><Verbatim text={r}/></li>)}</ul>}<details><summary>Review evidence</summary><AuditResult audit={a} replay/></details></article>)}</div></section></Localize>}
