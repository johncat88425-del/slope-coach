import {Verbatim} from './ModelHeadline.js';
import {useState} from 'react';
import type {AuditOut} from './audit.js';
import {cardDisplayLine,physicsCardLines,downloadPhysicsCard,shareCardContent} from './cardExport.js';
import {Localize,useTranslation} from './i18n.js';
export function PhysicsCard({audit,overlay,showDownload=true}:{audit:AuditOut;overlay?:string;showDownload?:boolean}){
 const t=useTranslation(),card=shareCardContent(audit);
 return <Localize><section data-testid="physics-card" className="physics-card" aria-label="Physics card"><h3>Physics card</h3><div className="share-card-preview" style={{background:card.background,color:card.ink}}><p>{card.verdict}</p>{card.provenance&&<p>{card.provenance}</p>}<strong className="share-value">{card.value} <small>{card.unit}</small></strong><p className="share-caption">{card.caption}</p>{card.secondary&&<div className="share-secondary"><p>{card.secondary.label} · <span>Grip limit: 1.2 g</span></p><strong>{card.secondary.value} {card.secondary.unit}</strong></div>}{card.limit&&!card.secondary&&<p>{card.limit}</p>}{card.reference&&<p><span>Estimated car length range (m):</span> {card.reference}</p>}{card.reason&&<p className="share-reason" data-testid="share-card-reason"><strong>Reason:</strong> <Verbatim text={card.reason}/></p>}<div className="share-badges"><span>{card.tracking}</span><span>{card.numbers}</span></div><p className="share-footer">{card.footer}</p></div><details><summary>Full card evidence</summary>{physicsCardLines(audit).map((line,i)=><p key={i}><Verbatim text={cardDisplayLine(audit,line,t)}/></p>)}{overlay&&<img className="track-overlay" src={overlay} alt="Backend tracking overlay thumbnail"/>}</details>{showDownload&&<PhysicsCardDownload audit={audit} overlay={overlay}/>}</section></Localize>
}

/** Shared local PNG export action; callers decide where the visible button belongs. */
export function PhysicsCardDownload({audit,overlay,label='Download physics card PNG'}:{audit:AuditOut;overlay?:string;label?:string}){
 const t=useTranslation(),[busy,setBusy]=useState(false),[error,setError]=useState('');
 return <Localize><div className="physics-card-action"><button className="share-download" data-testid="physics-card-download" disabled={busy} aria-busy={busy} onClick={async()=>{if(busy)return;setBusy(true);setError('');try{await downloadPhysicsCard(audit,overlay,t)}catch(error){setError(error instanceof Error?error.message:String(error))}finally{setBusy(false)}}}>{busy?'Preparing PNG…':label}</button>{error&&<p role="alert">{error}</p>}</div></Localize>;
}
