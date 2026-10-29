import {Verbatim} from './ModelHeadline.js';
import {Localize} from './i18n.js';
import {demoRecords} from './DemoCatalog';
import {verdictEnglish} from './audit';
export const openingKeys=['real_own_2','generated_meta_clip2','generated_meta_clip4'] as const;
export function OpeningCards(){return <Localize><section data-testid="reviewer-opening"><h2>Check motion against your assumed physical model.</h2><p>Inspect consistent, inconsistent and insufficient-data results with the evidence and limitations shown together.</p><div className="opening-cards">{openingKeys.map(key=>{const a=demoRecords.find(r=>r.key===key)?.audit;return a?<a key={key} data-testid="opening-card" href={'#examples/'+encodeURIComponent(key)}><strong>{verdictEnglish(a)}</strong><p>{a.explanation?<Verbatim text={a.explanation.text}/>:'Review the saved evidence.'}</p><span>{a.real_clip?'Recorded by john':'Generated test clip'}</span></a>:null})}</div></section></Localize>}
export function SavedExample({name}:{name:string|null}){const a=demoRecords.find(r=>r.key===name)?.audit;return a?<SavedResult audit={a} replay/>:<Localize><p role="alert">Saved example not found. Open the results wall to choose a record.</p></Localize>}
import {AuditResult as SavedResult} from './AuditPage';
