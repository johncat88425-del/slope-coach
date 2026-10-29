import {Verbatim} from './ModelHeadline.js';
import {useState} from 'react';
import type {AuditOut} from './audit.js';
import {cardDisplayLine,physicsCardLines,downloadPhysicsCard} from './cardExport.js';
import {Localize,useTranslation} from './i18n.js';
export function PhysicsCard({audit,overlay}:{audit:AuditOut;overlay?:string}){
 const t=useTranslation();
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 return <Localize><section data-testid="physics-card" className="physics-card" aria-label="Physics card"><h3>Physics card</h3>{physicsCardLines(audit).map((line,i)=><p key={i}><Verbatim text={cardDisplayLine(audit,line,t)}/></p>)}{overlay&&<img className="track-overlay" src={overlay} alt="Backend tracking overlay thumbnail"/>}<button data-testid="physics-card-download" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{await downloadPhysicsCard(audit,overlay)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}}>{busy?'Preparing PNG…':'Download physics card PNG'}</button>{error&&<p role="alert">{error}</p>}</section></Localize>
}
