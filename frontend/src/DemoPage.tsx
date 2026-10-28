import normal from '../../data/demo/synthetic_toss_normal_g.json?raw';
import inconsistent from '../../data/demo/synthetic_toss_quarter_g.json?raw';
import refused from '../../data/demo/synthetic_toss_moving_camera.json?raw';
import {parseSavedAudit} from './audit.js';
import {AuditResult} from './AuditPage.js';
import {Localize} from './i18n.js';
const cases=[normal,inconsistent,refused].map(parseSavedAudit);
export function DemoPage(){return <Localize><section data-testid="demo-comparison" className="demo-comparison"><h2>Three outcomes, one set of rules</h2><p role="status">SYNTHETIC — development fixtures made from program-drawn moving squares. These are not real experiment footage or evidence of real-video accuracy.</p><p>Consistent, inconsistent and insufficient-data results are shown together. Saved backend results are replayed without network calls or a new analysis.</p><div className="demo-grid">{cases.map(a=><div key={a.audit_id}><AuditResult audit={a} replay/></div>)}</div></section></Localize>}
