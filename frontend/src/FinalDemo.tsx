import type {AuditOut} from './audit.js';
import {AuditResult} from './AuditPage.js';
import {Localize} from './i18n.js';

type SavedEntry={key:string;audit:AuditOut};
export function FinalDemo({records,synthetic}:{records:SavedEntry[];synthetic:AuditOut[]}){
 const recorded=records.filter(({audit})=>audit.real_clip);
 const generated=records.filter(({audit})=>audit.generated_clip);
 return <Localize><section data-testid="demo-comparison" className="demo-comparison">
  <h1 className="page-title">Three outcomes, one set of rules</h1>
  <p>Consistent, inconsistent and insufficient-data results are shown together. Saved backend results are replayed without network calls or a new analysis.</p>
  <p>Each saved result retains its original measurements, explanation and source labels. All recorded and generated test clips are included.</p>
  <section data-testid="recorded-demo"><h2>John’s recorded experiments</h2>
   <p>Videos filmed by john; annotations confirmed by john. Every recorded experiment is retained, with its current saved outcome.</p>
   <p>Original videos are withheld for household privacy. These saved records show trajectories and measurements without loading video.</p>
   <div className="demo-grid">{recorded.map(({key,audit},i)=><article key={key} data-demo-key={key}><h3>Recorded clip {i+1}</h3><AuditResult audit={audit} replay/></article>)}</div>
  </section>
  <section data-testid="generated-demo"><h2>Generated test clips</h2>
   <p>These results compare motion with the selected model. The recorded reasons and limitations remain part of each result.</p>
   <div className="demo-grid">{generated.map(({key,audit},i)=><article key={key} data-demo-key={key}><h3>Generated test clip {i+1}</h3><AuditResult audit={audit} replay/></article>)}</div>
  </section>
  <details data-testid="synthetic-demo"><summary>Program-drawn test examples</summary>
   <p role="status">SYNTHETIC — program-drawn moving squares for development tests, separate from the recorded and generated clip results above.</p>
   <div className="demo-grid">{synthetic.map(audit=><article key={audit.audit_id}><AuditResult audit={audit} replay/></article>)}</div>
  </details>
 </section></Localize>;
}
