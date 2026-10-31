import {Verbatim} from './ModelHeadline.js';
import {Localize} from './i18n.js';
import {useState} from 'react';
import {demoRecords} from './DemoCatalog';
import {ModelSource} from './ModelSource';
export function HowItWorks(){const [key,setKey]=useState('real_own_2');const a=demoRecords.find(r=>r.key===key)?.audit;return <Localize><section data-testid="how-it-works" className="how-page"><p className="eyebrow">THE PROCESS</p><h1 className="page-title">From motion to evidence.</h1><p>Models ask questions and explain the result. Code calculates the measurements. If evidence is missing, the clip cannot be judged.</p>
 <ol className="process-steps">
 <li tabIndex={0}><span className="step-number" aria-hidden="true">01</span><h2>Confirm</h2><div className="step-description"><p>Muse Spark may ask questions (Meta model); fixed questions are marked mock when used. The actual source is shown in the interview panel and is not stored in this saved result.</p><p>Confirm the object, capture conditions and time window before running a check.</p></div></li>
 <li tabIndex={0}><span className="step-number" aria-hidden="true">02</span><h2>Track</h2><div className="step-description"><p>Follow the object through the selected segment. Tracking sources stay visible.</p>{a&&<ModelSource source={a.track_source} kind="tracking"/>}</div></li>
 <li tabIndex={0}><span className="step-number" aria-hidden="true">03</span><h2>Measure</h2><div className="step-description"><p>Code calculates motion from the tracked positions. Model text cannot change the measurements.</p></div></li>
 <li tabIndex={0}><span className="step-number" aria-hidden="true">04</span><h2>Explain</h2><div className="step-description"><p>The same quality checks are used for every clip. The result says whether the motion fits the selected model, or cannot be judged.</p>{a?.explanation?<><p>{a.explanation.source==='model'?'Meta model — Muse Spark':'Prepared explanation (no model)'}</p><p><Verbatim text={a.explanation.text}/></p></>:<p>No explanation source was supplied.</p>}</div></li>
 </ol><label className="source-picker">Inspect sources for a saved record<select value={key} onChange={e=>setKey(e.target.value)}>{demoRecords.map((r,i)=><option key={r.key} value={r.key}>Saved clip {i+1}</option>)}</select></label><a className="next primary" href="#audit">Check a video</a></section></Localize>}
