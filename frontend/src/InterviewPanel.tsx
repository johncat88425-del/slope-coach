import type {VehicleClass} from './vehiclePresentation.js';
import {AuditDimensionField,VehicleClassField} from './VehicleModel.js';
import {voiceFieldPatch} from './voiceAnswer.js';
import {ObjectSuggestionHint,suggestedObjectName} from './ObjectSuggestion.js';
import {createRequestGate} from './requestFeedback.js';
import {RequestStatus} from './RequestStatus.js';
import {WindowSuggestions} from './WindowSuggestions.js';
import {WindowSelector} from './WindowSelector.js';
import {VoiceAnswers} from './VoiceAnswers.js';
import {useEffect,useRef,useState} from 'react';
import type {createApi,AuditDraft,InterviewAnswers} from './api.js';
import {ApiError,friendlyApiError} from './api.js';
import type {AuditOut,AuditModel} from './audit.js';
import {validateAuditInput} from './audit.js';
import {Localize} from './i18n.js';
import {Verbatim} from './ModelHeadline.js';
import type {AuditStep} from './AuditSteps.js';
export function InterviewQuestions({draft}:{draft:AuditDraft}){return <Localize><div className="interview-questions" data-testid="interview-questions"><p className="source-label">{draft.interview.source==='model'?'Questions by Muse Spark':'Prepared questions (no model)'}</p>{draft.interview.note&&<p><Verbatim text={draft.interview.note}/></p>}<ol>{draft.interview.questions.map(q=><li key={q.field}><strong><Verbatim text={q.text}/></strong></li>)}</ol></div></Localize>}
export function InterviewPanel({api,onResult,disabled=false,onBusyChange,hasResult=false,onStepChange}:{api:ReturnType<typeof createApi>;onResult:(audit:AuditOut,source?:'model'|'mock')=>void;disabled?:boolean;onBusyChange?:(busy:boolean)=>void;hasResult?:boolean;onStepChange?:(step:AuditStep)=>void}){
 const requestGate=useRef(createRequestGate());
 const objectNameEdited=useRef(false),focusAnswers=useRef(false),objectInput=useRef<HTMLInputElement>(null),reviewGrid=useRef<HTMLDivElement>(null),errorBox=useRef<HTMLParagraphElement>(null);
 const [phase,setPhase]=useState<'preparing'|'checking'>('preparing'),[draftUsable,setDraftUsable]=useState(false);
 const [voiceBusy,setVoiceBusy]=useState(false);
 const [preview,setPreview]=useState(''),[windowConfirmed,setWindowConfirmed]=useState(false);
 const [file,setFile]=useState<File|null>(null),[draft,setDraft]=useState<AuditDraft|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [vehicleClass,setVehicleClass]=useState<VehicleClass|''>('');
 const [objectName,setObjectName]=useState('ball');
 const [camera,setCamera]=useState(''),[slow,setSlow]=useState(''),[model,setModel]=useState(''),[start,setStart]=useState(''),[end,setEnd]=useState(''),[size,setSize]=useState(''),[length,setLength]=useState('');
 useEffect(()=>{if(!file){setPreview('');return}const url=URL.createObjectURL(file);setPreview(url);return()=>URL.revokeObjectURL(url)},[file]);
 useEffect(()=>{onBusyChange?.(busy||voiceBusy)},[busy,voiceBusy,onBusyChange]);
 useEffect(()=>{if(focusAnswers.current&&draft&&!busy){focusAnswers.current=false;(reviewGrid.current?.querySelector<HTMLInputElement>('[data-testid="window-start"]')??objectInput.current)?.focus()}},[draft,busy]);
 useEffect(()=>{if(error)errorBox.current?.focus()},[error]);
 const step:AuditStep=busy?(phase==='checking'?2:0):draft?1:hasResult?3:0;
 useEffect(()=>{onStepChange?.(step)},[step,onStepChange]);
 async function prepare(){if(!file||busy||voiceBusy||disabled)return;await requestGate.current(async()=>{setBusy(true);setPhase('preparing');setError('');try{const next=await api.auditDraft(file);focusAnswers.current=true;setDraft(next);setObjectName(current=>suggestedObjectName(current,objectNameEdited.current,next.suggestion));setDraftUsable(true)}catch(e){setError(friendlyApiError(e))}finally{setBusy(false)}})}
 async function submit(){if(!draft||busy||voiceBusy||disabled)return;if(!draftUsable){setError('Prepare questions again before retrying. Your answers are kept.');return}const errors=validateAuditInput(start,end,size);if(!windowConfirmed)errors.push('Confirm the time window first.');if(!camera||!slow||!model)errors.push('Confirm camera, playback speed and motion model.');if(model==='vehicle'&&!vehicleClass)errors.push('Confirm the vehicle class, or choose Unknown.');if(model==='pendulum'&&length.trim()&&(!Number.isFinite(Number(length))||Number(length)<=0))errors.push('Pendulum length must be positive and finite; leave blank if unknown.');if(errors.length){setError(errors.join(' '));return}await requestGate.current(async()=>{setBusy(true);setPhase('checking');setError('');try{const answers:InterviewAnswers={object_name:objectName.trim()||'ball',t_start:Number(start),t_end:Number(end),camera_static:camera==='yes',slow_motion:slow==='yes',assumed_model:model as AuditModel};if(model==='vehicle'&&vehicleClass)answers.vehicle_class=vehicleClass;if(size.trim())answers.object_size_m=Number(size);if(model==='pendulum'&&length.trim())answers.length_m=Number(length);const result=await api.auditFromDraft(draft.draft_id,answers);setDraft(null);setDraftUsable(false);onResult(result,draft.interview.source)}catch(e){setError(friendlyApiError(e));if(!(e instanceof ApiError)||e.status===404)setDraftUsable(false)}finally{setBusy(false)}})}
 return <Localize><details className="interview-panel" open={!hasResult} data-testid="interview-panel">
  <summary>Muse interview — confirm before checking</summary>
  <fieldset className="upload-area" disabled={busy||voiceBusy||disabled}>
   <legend className="sr-only">Interview video</legend>
   <div className="upload-actions">
    <p className="eyebrow">YOUR CLIP</p><h2>Choose a video to begin</h2>
    <label className={'video-picker'+(file?' is-selected':'')}><span>{file?'Choose another video':'Choose video'}</span>
     <input data-testid="interview-video" aria-label="Interview video" type="file" accept="video/*" onChange={e=>{objectNameEdited.current=false;setObjectName('ball');setFile(e.target.files?.[0]??null);setDraft(null);setDraftUsable(false);setCamera('');setSlow('');setModel('');setVehicleClass('');setStart('');setEnd('');setWindowConfirmed(false);setSize('');setLength('');setError('')}}/>
    </label>
    {file&&<p className="selected-file"><Verbatim text={file.name}/></p>}
    <button className="primary" data-testid="interview-prepare" hidden={!file} disabled={!file||busy||disabled} onClick={()=>void prepare()}>Prepare questions</button>
    <p className="upload-note">Local preview · user-confirmed inputs</p>
   </div>
   {!draft&&<figure className="upload-example">
    {preview?<video aria-label="Selected video preview" controls src={preview}/>:<img src={(import.meta.env?.BASE_URL??'/')+'images/motion-study.jpg'} width="1280" height="720" alt="A frame from a Meta AI–generated test clip (meta_clip4)"/>}
    <figcaption>{file?'Review your selected clip before preparing questions.':'A frame from one of our Meta AI test clips. Start with your own clip.'}</figcaption>
   </figure>}
   {draft&&<div ref={reviewGrid} className="interview-grid">
    {preview&&<WindowSelector key={preview} url={preview} start={start} end={end} confirmed={windowConfirmed} onChange={(s,e)=>{setStart(s);setEnd(e);setWindowConfirmed(false)}} onConfirm={()=>setWindowConfirmed(true)}><WindowSuggestions key={draft.draft_id+objectName} api={api} objectName={objectName} prepare={async()=>draft.draft_id} onSelect={(s,e)=>{setStart(s);setEnd(e);setWindowConfirmed(false)}}/></WindowSelector>}
    <div className="interview-answers">
     <h2>Confirm the conditions</h2><InterviewQuestions draft={draft}/>
     <p>Questions guide your review. Only your confirmed answers are sent as measurements and capture conditions.</p>
     <label>Object name<input ref={objectInput} data-testid="interview-object-name" value={objectName} onChange={e=>{objectNameEdited.current=true;setObjectName(e.target.value)}}/></label>
     <ObjectSuggestionHint suggestion={draft.suggestion}/>
     <label>Camera remained fixed<select data-testid="interview-camera" value={camera} onChange={e=>setCamera(e.target.value)}><option value="">Choose…</option><option value="yes">Yes</option><option value="no">No</option></select></label>
     <label>Slow motion or retimed playback<select data-testid="interview-slow" value={slow} onChange={e=>setSlow(e.target.value)}><option value="">Choose…</option><option value="yes">Yes</option><option value="no">No</option></select></label>
     <label>Motion model<select data-testid="interview-model" value={model} onChange={e=>setModel(e.target.value)}><option value="">Choose…</option><option value="free_flight">Free flight</option><option value="bounce">Bounce</option><option value="pendulum">Pendulum</option><option value="vehicle">Car driving past side-on (fixed camera)</option></select></label>
     {model==='vehicle'&&<VehicleClassField value={vehicleClass} onChange={setVehicleClass}/>}
     <AuditDimensionField model={model} value={size} onChange={setSize}/>
     {model==='pendulum'&&<label>Pendulum length (metres, optional)<input type="number" step="any" min="0" value={length} onChange={e=>setLength(e.target.value)}/></label>}
     <button className="primary" data-testid="interview-submit" disabled={!windowConfirmed||!draftUsable||busy||disabled} onClick={()=>void submit()}>Confirm and check</button>
    </div>
   </div>}
  </fieldset>
  {draft&&<details className="voice-drawer"><summary>Optional voice answer</summary><VoiceAnswers key={draft.draft_id} api={api} draftId={draft.draft_id} source={draft.interview.source} disabled={busy||disabled||!draftUsable} onBusyChange={setVoiceBusy} onUse={(field,value)=>{
   const patch=voiceFieldPatch(field,value);if(!patch)return;
   if(patch.camera!==undefined)setCamera(patch.camera);
   if(patch.slow!==undefined)setSlow(patch.slow);
   if(patch.model!==undefined)setModel(patch.model);
   if(patch.size!==undefined)setSize(patch.size);
   if(patch.length!==undefined)setLength(patch.length);
   if(patch.start!==undefined&&patch.end!==undefined){setStart(patch.start);setEnd(patch.end);setWindowConfirmed(false)}
  }}/></details>}
  {busy&&<RequestStatus phase={phase}/>}{error&&<p ref={errorBox} tabIndex={-1} role="alert">{error}</p>}
 </details></Localize>
}
