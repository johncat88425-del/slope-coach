import {Verbatim} from './ModelHeadline.js';
import {useState} from 'react';
import type {AuditOut} from './audit.js';
import {cardDisplayLine,physicsCardLines,downloadPhysicsCard,shareCardContent} from './cardExport.js';
import {Localize,useTranslation} from './i18n.js';
export function PhysicsCard({audit,overlay}:{audit:AuditOut;overlay?:string}){
 const t=useTranslation(),card=shareCardContent(audit);
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 return <Localize><section data-testid="physics-card" className="physics-card" aria-label="Physics card"><h3>Physics card</h3><div className="share-card-preview" style={{background:card.background,color:card.ink}}><p>{card.verdict}</p>{card.provenance&&<p>{card.provenance}</p>}<strong className="share-value">{card.value} <small>{card.unit}</small></strong><p className="share-caption">{card.caption}</p>{card.secondary&&<div className="share-secondary"><p>{card.secondary.label} · <span>Grip limit: 1.2 g</span></p><strong>{card.secondary.value} {card.secondary.unit}</strong></div>}{card.limit&&!card.secondary&&<p>{card.limit}</p>}{card.reference&&<p><span>Estimated car length range (m):</span> {card.reference}</p>}<div className="share-badges"><span>{card.tracking}</span><span>{card.numbers}</span></div><p className="share-footer">{card.footer}</p></div><details><summary>Full card evidence</summary>{physicsCardLines(audit).map((line,i)=><p key={i}><Verbatim text={cardDisplayLine(audit,line,t)}/></p>)}{overlay&&<img className="track-overlay" src={overlay} alt="Backend tracking overlay thumbnail"/>}</details><button data-testid="physics-card-download" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{await downloadPhysicsCard(audit,overlay,t)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}}>{busy?'Preparing PNG…':'Download physics card PNG'}</button>{error&&<p role="alert">{error}</p>}</section></Localize>
}
