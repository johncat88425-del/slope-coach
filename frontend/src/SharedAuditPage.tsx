import {useEffect,useState} from 'react';
import {AuditResult} from './AuditPage.js';
import {ApiErrorNotice} from './ApiErrorNotice.js';
import {decodeSharedAudit} from './sharedAudit.js';
import {Localize} from './i18n.js';

export function SharedAuditPage({payload}:{payload:string}){
 const [result,setResult]=useState<Awaited<ReturnType<typeof decodeSharedAudit>>|null>(null),[error,setError]=useState<unknown>(null);
 useEffect(()=>{let active=true;setResult(null);setError(null);void decodeSharedAudit(payload).then(value=>{if(active)setResult(value)}).catch(value=>{if(active)setError(value)});return()=>{active=false}},[payload]);
 return <Localize><section aria-label="Shared result" data-testid="shared-audit-page">
  <h1>Shared saved result</h1><p>Saved result replay — no new analysis or model call.</p>
  {result?.pathReduced&&<p>The drawing path was simplified for sharing. The original JSON contains the full record.</p>}
  {!result&&!error&&<p role="status">Opening the saved result…</p>}
  <ApiErrorNotice error={error}/>{result&&<AuditResult audit={result.audit} sampleKind={result.audit.synthetic?'synthetic':result.audit.generated_clip?'generated':null} replay autoFocus/>}
 </section></Localize>;
}
