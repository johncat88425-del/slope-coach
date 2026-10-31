import {Localize} from './i18n.js';
import type {AuditOut} from './audit.js';
import {HomeMotion} from './HomeMotion.js';
export function Home({example}:{example?:AuditOut}){return <Localize><section className="home-page" aria-label="Tool scope">
 <div className="home-hero"><div className="hero-copy"><p className="eyebrow">VIDEO PHYSICS AUDIT</p>
 <h1>Does it fall like <em>Earth?</em></h1>
 <p className="hero-description">Check whether the motion in a video fits your assumed physical model.</p>
 <div className="hero-actions"><a data-testid="home-audit" className="next primary" href="#audit">Check a video</a><a className="next" href="#wall">See examples</a></div>
 <p className="hero-footnote">Your clip. Your assumptions. The evidence, explained.</p></div>
 <HomeMotion audit={example}/></div>
 <details className="scope-notes"><summary>Scope and limitations</summary><h3>What this version checks</h3><ul><li>A user-selected free-flight segment under a fixed, approximately side-on camera.</li><li>Observed motion against the stated model, with reasons, backend numbers, tracking overlays and known limitations.</li><li>Evidence quality: missing observations can lead to an insufficient-data outcome.</li></ul>
 <h3>What it cannot establish</h3><ul><li>It does not establish a clip’s provenance or authenticity.</li><li>It does not support arbitrary camera motion, perspective changes or every physical situation.</li><li>It does not directly measure hidden forces or internal material stresses.</li></ul>
 <h3>Before uploading</h3><p>Use a fixed camera, keep the object visible, select the relevant movement, and enter only dimensions you have measured. Leave unknown dimensions blank. Replayed, retimed or perspective-distorted footage may not meet the assumptions.</p>
 <h3>Where the evidence comes from</h3><p>Code calculates the measurements and checks the motion. Muse Spark and SAM 3.1 are credited only when used. Prepared or manual results keep their own labels.</p><p>This check supports a limited set of capture conditions and motion models. Performance on recorded experiments remains under evaluation.</p>
 <a data-testid="home-coach" className="next" href="#setup">Open slope experiment coach →</a></details>
 </section></Localize>}
