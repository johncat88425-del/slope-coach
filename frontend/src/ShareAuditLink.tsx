import {useEffect,useState} from 'react';
import type {AuditOut} from './audit.js';
import {buildAuditShareLink} from './sharedAudit.js';
import type {AuditShareLink} from './sharedAudit.js';
import {Localize} from './i18n.js';

export function ShareAuditLink({audit}:{audit:AuditOut}){
 const [prepared,setPrepared]=useState<{audit:AuditOut;link:AuditShareLink}|null>(null),[status,setStatus]=useState('');
 const link=prepared?.audit===audit?prepared.link:null;
 useEffect(()=>{let active=true;setStatus('');void buildAuditShareLink(audit,location.origin,import.meta.env?.BASE_URL??'/').then(link=>{if(active)setPrepared({audit,link})});return()=>{active=false}},[audit]);
 return <Localize><div className="audit-share-link" data-testid="audit-share-link">
  {link&&<a href={link.url}>Open result link</a>}
  <button data-testid="copy-audit-link" disabled={!link} onClick={async()=>{if(!link)return;try{await navigator.clipboard.writeText(link.url);setStatus('Link copied.')}catch{setStatus('Could not copy. Use the result link.')}}}>Copy link</button>
  <span role="status">{link?status:'Preparing share link…'}</span>
  {link&&<small className="share-link-note" data-testid="share-link-note">{link.embedded?'This link contains the saved result and works after a server restart. Video is not included.':'This result is too large or compressed links are unavailable. This server link expires after a restart; save the JSON.'}</small>}
 </div></Localize>;
}
