import {Localize} from './i18n.js';
import {useState} from 'react';
import {demoRecords} from './DemoCatalog';
import {AuditResult} from './AuditPage';
import {comparisonKeys} from './demoSelection.js';
export function PairComparison(){const [left,setLeft]=useState<string>(comparisonKeys[0]),[right,setRight]=useState<string>(comparisonKeys[1]);return <Localize><section data-testid="pair-comparison"><h1 className="page-title">Same rules, two clips</h1><p>Select any two saved records. Source labels describe origin; results compare motion with the assumed model.</p><div className="pair-grid">{[{value:left,set:setLeft,label:'Left clip'},{value:right,set:setRight,label:'Right clip'}].map(({value,set,label})=>{const entry=demoRecords.find(r=>r.key===value);return <div key={label} data-demo-key={entry?.key}><label>{label}<select value={value} onChange={e=>set(e.target.value)}>{demoRecords.map((r,i)=><option key={r.key} value={r.key}>Saved clip {i+1}</option>)}</select></label>{entry&&<><p>{entry.audit.real_clip?'Recorded by john; annotations confirmed by john.':'Generated test clip'}</p><AuditResult key={entry.key} audit={entry.audit} replay/></>}</div>})}</div></section></Localize>}
