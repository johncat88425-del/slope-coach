import own1 from '../../data/demo/real_own_1.json?raw';
import own2 from '../../data/demo/real_own_2.json?raw';
import own3 from '../../data/demo/real_own_3.json?raw';
import normal from '../../data/demo/synthetic_toss_normal_g.json?raw';
import inconsistent from '../../data/demo/synthetic_toss_quarter_g.json?raw';
import refused from '../../data/demo/synthetic_toss_moving_camera.json?raw';
import {parseSavedAudit} from './audit.js';
import {AuditResult} from './AuditPage.js';
import {Localize} from './i18n.js';
const cases=[normal,inconsistent,refused].map(parseSavedAudit);
const recorded=[own1,own2,own3].map(parseSavedAudit);
export function DemoPage(){return <Localize><section data-testid="demo-comparison" className="demo-comparison"><section data-testid="recorded-demo"><h2>John’s recorded experiments</h2><p>Videos filmed by john; annotations confirmed by john. All three records are shown, including the inconsistent result whose cause remains unknown.</p><p>Original videos are withheld for household privacy. These saved records show trajectories and measurements without loading video.</p><div className="demo-grid">{recorded.map((a,i)=><div key={a.audit_id}><h3>own_{i+1}</h3>{i===2&&<p>Inconsistent with the assumed model; cause unknown. This result does not establish a cause.</p>}<AuditResult audit={a} replay/></div>)}</div></section><h2>Three outcomes, one set of rules</h2><p role="status">SYNTHETIC — test examples made from program-drawn moving squares. Performance on recorded experiments remains unverified.</p><p>Consistent, inconsistent and insufficient-data results are shown together. Saved backend results are replayed without network calls or a new analysis.</p><div className="demo-grid">{cases.map(a=><div key={a.audit_id}><AuditResult audit={a} replay/></div>)}</div></section></Localize>}
