import {useEffect,useId,useRef,useState} from 'react';
import type {AuditDraft,SampleClip,createApi} from './api.js';
import {isTemporaryApiError} from './api.js';
import {ApiErrorNotice} from './ApiErrorNotice.js';
import {createRequestGate} from './requestFeedback.js';
import {RequestStatus} from './RequestStatus.js';
import {Localize} from './i18n.js';
import {Verbatim} from './ModelHeadline.js';
import {DEMO_ONLY} from './mode.js';
export function SamplePicker({api,disabled=false,onDraft,onBusyChange,onStart}:{api:ReturnType<typeof createApi>;disabled?:boolean;onDraft:(draft:AuditDraft,sample:SampleClip)=>void;onBusyChange:(busy:boolean)=>void;onStart?:()=>void}){
 const [samples,setSamples]=useState<SampleClip[]|null>(null),[phase,setPhase]=useState<'list'|'draft'|null>(null),[error,setError]=useState<unknown>(null),[retry,setRetry]=useState<'list'|SampleClip|null>(null);
 const gate=useRef(createRequestGate()),listId=useId();
 useEffect(()=>{onBusyChange(phase!==null)},[phase,onBusyChange]);
 async function load(){if(disabled||phase)return;await gate.current(async()=>{setPhase('list');setError(null);setRetry(null);try{setSamples(await api.sampleClips())}catch(e){setError(e);if(isTemporaryApiError(e))setRetry('list')}finally{setPhase(null)}})}
 async function choose(sample:SampleClip){if(disabled||phase)return;await gate.current(async()=>{setPhase('draft');setError(null);setRetry(null);onStart?.();try{onDraft(await api.sampleDraft(sample.name),sample)}catch(e){setError(e);if(isTemporaryApiError(e))setRetry(sample)}finally{setPhase(null)}})}
 return DEMO_ONLY?null:<Localize><section className="sample-picker" data-testid="sample-picker" aria-label="Sample clips">
  <button data-testid="try-sample" disabled={disabled||phase!==null} aria-expanded={samples!==null} aria-controls={listId} onClick={()=>void load()}>Try a sample clip</button>
  {phase==='list'&&<p role="status">Loading sample clips…</p>}
  {phase==='draft'&&<RequestStatus phase="preparing"/>}
  {samples!==null&&<div id={listId}><p>Choose a clip. Confirm its conditions before checking.</p>{samples.length?<ul>{samples.map(sample=><li key={sample.name}><span className="source-label">{sample.kind==='synthetic'?'Synthetic test clip':'Generated test clip'}</span><button data-testid="choose-sample" disabled={disabled||phase!==null} onClick={()=>void choose(sample)}><Verbatim text={sample.label}/></button></li>)}</ul>:<p>No sample clips are available.</p>}</div>}
  <ApiErrorNotice error={error} disabled={disabled||phase!==null} onRetry={retry?()=>void(retry==='list'?load():choose(retry)):undefined}/>
 </section></Localize>;
}
