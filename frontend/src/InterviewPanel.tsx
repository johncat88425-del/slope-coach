import {SamplePicker} from './SamplePicker.js';
import {mediaUrl} from './media.js';
import type {VehicleClass} from './vehiclePresentation.js';
import {AuditDimensionField,VehicleClassField} from './VehicleModel.js';
import {voiceFieldPatch} from './voiceAnswer.js';
import {ObjectSuggestionHint,suggestedObjectName,suggestedVehicleFields} from './ObjectSuggestion.js';
import {createRequestGate} from './requestFeedback.js';
import {RequestStatus} from './RequestStatus.js';
import {WindowSuggestions} from './WindowSuggestions.js';
import {WindowSelector} from './WindowSelector.js';
import {VoiceAnswers} from './VoiceAnswers.js';
import {useEffect,useRef,useState} from 'react';
import type {createApi,AuditDraft,InterviewAnswers,SampleClip} from './api.js';
import {ApiError,isTemporaryApiError} from './api.js';
import {ApiErrorNotice} from './ApiErrorNotice.js';
import type {AuditOut,AuditModel} from './audit.js';
import {validateAuditInput} from './audit.js';
import {Localize} from './i18n.js';
import {Verbatim} from './ModelHeadline.js';
import type {AuditStep} from './AuditSteps.js';
export function InterviewQuestions({draft}:{draft:AuditDraft}){return <Localize><div className="interview-questions" data-testid="interview-questions"><p className="source-label">{draft.interview.source==='model'?'Questions by Muse Spark':'Prepared questions (no model)'}</p>{draft.interview.note&&<p><Verbatim text={draft.interview.note}/></p>}<ol>{draft.interview.questions.map(q=><li key={q.field}><strong><Verbatim text={q.text}/></strong></li>)}</ol></div></Localize>}
export function InterviewPanel({api,onResult,disabled=false,onBusyChange,hasResult=false,onStepChange,onNewSource}:{api:ReturnType<typeof createApi>;onResult:(audit:AuditOut,source?:'model'|'mock',sampleKind?:SampleClip['kind'])=>void;disabled?:boolean;onBusyChange?:(busy:boolean)=>void;hasResult?:boolean;onStepChange?:(step:AuditStep)=>void;onNewSource?:()=>void}){
 const requestGate=useRef(createRequestGate());
 const modelEdited=useRef(false),vehicleClassEdited=useRef(false);
 const objectNameEdited=useRef(false),focusAnswers=useRef(false),objectInput=useRef<HTMLInputElement>(null),reviewGrid=useRef<HTMLDivElement>(null);
 const [retry,setRetry]=useState<'prepare'|'submit'|null>(null);
 const [phase,setPhase]=useState<'preparing'|'checking'>('preparing'),[draftUsable,setDraftUsable]=useState(false);
 const [voiceBusy,setVoiceBusy]=useState(false),[sampleBusy,setSampleBusy]=useState(false),[sample,setSample]=useState<SampleClip|null>(null);
 const [preview,setPreview]=useState(''),[windowConfirmed,setWindowConfirmed]=useState(false);
 const [file,setFile]=useState<File|null>(null),[draft,setDraft]=useState<AuditDraft|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState<unknown>(null);
 const [vehicleClass,setVehicleClass]=useState<VehicleClass|''>('');
 const [objectName,setObjectName]=useState('ball');
 const [camera,setCamera]=useState(''),[slow,setSlow]=useState(''),[model,setModel]=useState(''),[start,setStart]=useState(''),[end,setEnd]=useState(''),[size,setSize]=useState(''),[length,setLength]=useState('');
 useEffect(()=>{if(!file){setPreview('');return}const url=URL.createObjectURL(file);setPreview(url);return()=>URL.revokeObjectURL(url)},[file]);
 useEffect(()=>{onBusyChange?.(busy||voiceBusy||sampleBusy)},[busy,voiceBusy,sampleBusy,onBusyChange]);
 useEffect(()=>{if(focusAnswers.current&&draft&&!busy&&!sampleBusy&&!voiceBusy&&!disabled){focusAnswers.current=false;(reviewGrid.current?.querySelector<HTMLInputElement>('[data-testid="window-start"]')??objectInput.current)?.focus()}},[draft,busy,sampleBusy,voiceBusy,disabled]);
 const clipPreview=sample?mediaUrl(draft?.video_url,import.meta.env?.VITE_API_BASE_URL)??'':preview;
 const step:AuditStep=busy?(phase==='checking'?2:0):draft?1:hasResult?3:0;
 useEffect(()=>{onStepChange?.(step)},[step,onStepChange]);
 async function prepare(){if(!file||busy||voiceBusy||sampleBusy||disabled)return;await requestGate.current(async()=>{setBusy(true);setPhase('preparing');setError(null);setRetry(null);try{const next=await api.auditDraft(file);focusAnswers.current=true;setDraft(next);setObjectName(current=>suggestedObjectName(current,objectNameEdited.current,next.suggestion));const fields=suggestedVehicleFields({model,vehicleClass},{model:modelEdited.current,vehicleClass:vehicleClassEdited.current},next.suggestion);setModel(fields.model);setVehicleClass(fields.vehicleClass);setDraftUsable(true)}catch(e){setError(e);if(isTemporaryApiError(e))setRetry('prepare')}finally{setBusy(false)}})}
 async function submit(){if(!draft||busy||voiceBusy||sampleBusy||disabled)return;if(!draftUsable){setError('Prepare questions again before retrying. Your answers are kept.');return}const errors=validateAuditInput(start,end,size);if(!windowConfirmed)errors.push('Confirm the time window first.');if(!camera||!slow||!model)errors.push('Confirm camera, playback speed and motion model.');if(model==='vehicle'&&!vehicleClass)errors.push('Confirm the vehicle class, or choose Unknown.');if(model==='pendulum'&&length.trim()&&(!Number.isFinite(Number(length))||Number(length)<=0))errors.push('Pendulum length must be positive and finite; leave blank if unknown.');if(errors.length){setError(errors.join(' '));return}await requestGate.current(async()=>{setBusy(true);setPhase('checking');setError(null);setRetry(null);try{const answers:InterviewAnswers={object_name:objectName.trim()||'ball',t_start:Number(start),t_end:Number(end),camera_static:camera==='yes',slow_motion:slow==='yes',assumed_model:model as AuditModel};if(model==='vehicle'&&vehicleClass)answers.vehicle_class=vehicleClass;if(size.trim())answers.object_size_m=Number(size);if(model==='pendulum'&&length.trim())answers.length_m=Number(length);const result=await api.auditFromDraft(draft.draft_id,answers);setDraft(null);setDraftUsable(false);onResult(result,draft.interview.source,sample?.kind)}catch(e){setError(e);if(isTemporaryApiError(e))setRetry('submit');if(!(e instanceof ApiError)||e.status===404)setDraftUsable(false)}finally{setBusy(false)}})}
 function acceptSample(next:AuditDraft,clip:SampleClip){
  objectNameEdited.current=false;modelEdited.current=false;vehicleClassEdited.current=false;focusAnswers.current=true;
  setFile(null);setSample(clip);setDraft(next);setDraftUsable(true);setCamera('');setSlow('');setStart('');setEnd('');setWindowConfirmed(false);setSize('');setLength('');setError(null);setRetry(null);
  setObjectName(suggestedObjectName('ball',false,next.suggestion));
  const fields=suggestedVehicleFields({model:'',vehicleClass:''},{model:false,vehicleClass:false},next.suggestion);setModel(fields.model);setVehicleClass(fields.vehicleClass);
 }
 return <Localize><details className="interview-panel" open={!hasResult} data-testid="interview-panel">
  <summary>Muse interview — confirm before checking</summary>
  <fieldset className="upload-area" disabled={busy||voiceBusy||sampleBusy||disabled}>
   <legend className="sr-only">Interview video</legend>
   <div className="upload-actions">
    <p className="eyebrow">YOUR CLIP</p><h2 data-testid="interview-upload-title">{file||sample?'Review your selected clip':'Choose a video to begin'}</h2>
    <label className={'video-picker'+(file||sample?' is-selected':'')}><span>{file||sample?'Choose another video':'Choose video'}</span>
     <input data-testid="interview-video" aria-label="Interview video" type="file" accept="video/*" onChange={e=>{onNewSource?.();setSample(null);objectNameEdited.current=false;modelEdited.current=false;vehicleClassEdited.current=false;setObjectName('ball');setFile(e.target.files?.[0]??null);setDraft(null);setDraftUsable(false);setCamera('');setSlow('');setModel('');setVehicleClass('');setStart('');setEnd('');setWindowConfirmed(false);setSize('');setLength('');setError('')}}/>
    </label>
    {file&&<p className="selected-file"><Verbatim text={file.name}/></p>}
    <button className="primary" data-testid="interview-prepare" hidden={!file} disabled={!file||busy||disabled} onClick={()=>void prepare()}>Prepare questions</button>
    <SamplePicker api={api} disabled={busy||voiceBusy||disabled} onBusyChange={setSampleBusy} onDraft={acceptSample} onStart={onNewSource}/>
    {sample&&<p className="selected-file" data-testid="selected-sample"><span>{sample.kind==='synthetic'?'Synthetic test clip':'Generated test clip'}</span> · <Verbatim text={sample.label}/></p>}
    <p className="upload-note">Video preview · user-confirmed inputs</p>
   </div>
   {!draft&&<figure className="upload-example">
    {clipPreview?<video aria-label="Selected video preview" controls src={clipPreview}/>:<img src={(import.meta.env?.BASE_URL??'/')+'images/motion-study.jpg'} width="1280" height="720" alt="A frame from a Meta AI–generated test clip (meta_clip4)"/>}
    <figcaption>{file?'Review your selected clip before preparing questions.':'A frame from one of our Meta AI test clips. Start with your own clip.'}</figcaption>
   </figure>}
   {draft&&<div ref={reviewGrid} className="interview-grid">
    {clipPreview&&<WindowSelector key={clipPreview} url={clipPreview} start={start} end={end} confirmed={windowConfirmed} onChange={(s,e)=>{setStart(s);setEnd(e);setWindowConfirmed(false)}} onConfirm={()=>setWindowConfirmed(true)}><WindowSuggestions key={draft.draft_id+objectName} api={api} objectName={objectName} prepare={async()=>draft.draft_id} onSelect={(s,e)=>{setStart(s);setEnd(e);setWindowConfirmed(false)}}/></WindowSelector>}
    {sample&&!clipPreview&&<p role="alert">The sample preview is unavailable. Choose another clip.</p>}
    <div className="interview-answers">
     <h2>Confirm the conditions</h2><InterviewQuestions draft={draft}/>
     <p>Questions guide your review. Only your confirmed answers are sent as measurements and capture conditions.</p>
     <label>Object name<input ref={objectInput} data-testid="interview-object-name" value={objectName} onChange={e=>{objectNameEdited.current=true;setObjectName(e.target.value)}}/></label>
     <ObjectSuggestionHint suggestion={draft.suggestion}/>
     <label>Camera remained fixed<select data-testid="interview-camera" value={camera} onChange={e=>setCamera(e.target.value)}><option value="">Choose…</option><option value="yes">Yes</option><option value="no">No</option></select></label>
     <label>Slow motion or retimed playback<select data-testid="interview-slow" value={slow} onChange={e=>setSlow(e.target.value)}><option value="">Choose…</option><option value="yes">Yes</option><option value="no">No</option></select></label>
     <label>Motion model<select data-testid="interview-model" value={model} onChange={e=>{modelEdited.current=true;setModel(e.target.value)}}><option value="">Choose…</option><option value="free_flight">Free flight</option><option value="bounce">Bounce</option><option value="pendulum">Pendulum</option><option value="vehicle">Car driving past side-on (fixed camera)</option></select></label>
     {model==='vehicle'&&<VehicleClassField value={vehicleClass} onChange={value=>{vehicleClassEdited.current=true;setVehicleClass(value)}}/>}
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
   if(patch.model!==undefined){modelEdited.current=true;setModel(patch.model)}
   if(patch.size!==undefined)setSize(patch.size);
   if(patch.length!==undefined)setLength(patch.length);
   if(patch.start!==undefined&&patch.end!==undefined){setStart(patch.start);setEnd(patch.end);setWindowConfirmed(false)}
  }}/></details>}
  {busy&&<RequestStatus phase={phase}/>}<ApiErrorNotice error={error} disabled={busy||voiceBusy||sampleBusy||disabled} onRetry={retry?()=>void(retry==='prepare'?prepare():submit()):undefined}/>
 </details></Localize>
}
