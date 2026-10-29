import {useEffect,useRef,useState} from 'react';
import type {createApi,InterviewField,VoiceAnswer,VoiceField} from './api.js';
import {friendlyApiError} from './api.js';
import {Localize,useTranslation} from './i18n.js';
import {Verbatim} from './ModelHeadline.js';
import {RequestStatus} from './RequestStatus.js';
import {parseVoiceAnswer,voiceAudioFile,voiceFieldLabels} from './voiceAnswer.js';
import {startVoiceRecording,type VoiceRecording} from './voiceRecorder.js';

type UseField=(field:InterviewField,value:VoiceField['value'])=>void;
export function VoiceReview({answer,onUse,disabled=false}:{answer:VoiceAnswer;onUse:UseField;disabled?:boolean}){
 const [used,setUsed]=useState<Partial<Record<InterviewField,boolean>>>({});
 return <Localize><section data-testid="voice-review"><h4>Transcript</h4>
 <p>{answer.source.transcript==='mock'?'No transcription model used':'Transcribed by Muse Voice Transcribe'}</p>
 <p><Verbatim text={answer.transcript}/></p>
 <p>{answer.source.fields==='mock'?'No field extraction model used':'Fields suggested by Muse Spark'}</p>
 {Object.keys(answer.fields).length>0&&<p>Review each value. Use this copies only that field; it does not submit the check.</p>}
 {Object.entries(answer.fields).map(([name,entry])=>{const field=name as InterviewField;return <div key={field} data-testid={'voice-field-'+field}>
  <p><strong>{voiceFieldLabels[field]}</strong>: <output>{Array.isArray(entry!.value)?entry!.value.join(' – '):typeof entry!.value==='boolean'?(entry!.value?'Yes':'No'):String(entry!.value)}</output></p>
  <button type="button" disabled={disabled||used[field]||answer.source.fields==='mock'} onClick={()=>{onUse(field,entry!.value);setUsed(v=>({...v,[field]:true}))}}>{used[field]?'Used':'Use this'} <span className="sr-only">{voiceFieldLabels[field]}</span></button>
 </div>})}
 {!Object.keys(answer.fields).length&&<p>No fields were extracted. Please use the form fields.</p>}
 </section></Localize>;
}

export function VoiceAnswers({api,draftId,source='mock',onUse,disabled=false,onBusyChange}:{api?:ReturnType<typeof createApi>;draftId?:string;source?:'model'|'mock';onUse?:UseField;disabled?:boolean;onBusyChange?:(busy:boolean)=>void}){
 const t=useTranslation();
 const [phase,setPhase]=useState<'idle'|'starting'|'recording'|'sending'>('idle');
 const [recorded,setRecorded]=useState<Blob|null>(null),[preview,setPreview]=useState(''),[answer,setAnswer]=useState<VoiceAnswer|null>(null),[reviewVersion,setReviewVersion]=useState(0),[mock,setMock]=useState(false),[error,setError]=useState('');
 const active=useRef(true),lock=useRef(false),recording=useRef<VoiceRecording|null>(null);
 const available=source==='model'&&!mock&&Boolean(api&&draftId&&onUse),busy=phase!=='idle';
 useEffect(()=>{active.current=true;return()=>{active.current=false;recording.current?.cancel()}},[]);
 useEffect(()=>{onBusyChange?.(busy);return()=>onBusyChange?.(false)},[busy,onBusyChange]);
 useEffect(()=>{if(!recorded){setPreview('');return}const url=URL.createObjectURL(recorded);setPreview(url);return()=>URL.revokeObjectURL(url)},[recorded]);
 async function start(){
  if(!available||disabled||lock.current)return;
  lock.current=true;setPhase('starting');setError('');
  try{
   if(typeof MediaRecorder==='undefined'||!navigator.mediaDevices?.getUserMedia)throw new Error('Recording is unavailable in this browser. Please use the form fields.');
   const session=await startVoiceRecording();
   if(!active.current){session.cancel();return}
   recording.current=session;setRecorded(null);setAnswer(null);setPhase('recording');
   try{const blob=await session.finished;if(active.current)setRecorded(blob)}
   catch(e){if(active.current)setError(e instanceof Error?e.message:String(e))}
  }catch(e){if(active.current)setError(e instanceof DOMException&&e.name==='NotAllowedError'?'Microphone access was not granted. Please use the form fields.':e instanceof Error?e.message:String(e))}
  finally{recording.current=null;lock.current=false;if(active.current)setPhase('idle')}
 }
 async function send(){
  if(!available||disabled||lock.current||!recorded||!api||!draftId)return;
  lock.current=true;setPhase('sending');setError('');
  try{const result=parseVoiceAnswer(await api.voiceAnswer(draftId,voiceAudioFile(recorded)));if(active.current){setAnswer(result);setReviewVersion(v=>v+1);setMock(result.source.transcript==='mock'||result.source.fields==='mock')}}
  catch(e){if(active.current)setError(friendlyApiError(e))}
  finally{lock.current=false;if(active.current)setPhase('idle')}
 }
 return <Localize><section className="voice-answers" data-testid="voice-answers"><h3>Voice answers</h3>
 <button type="button" data-testid="voice-record" disabled={!available||busy||disabled} onClick={()=>void start()}>{available?'Record answer':'Record answer — requires Meta API'}</button>
 {!available&&<p>No microphone access or recording is started. Voice answers require Meta API.</p>}
 {phase==='starting'&&<p role="status">Waiting for microphone permission…</p>}
 {phase==='recording'&&<><p role="status">Recording your answer…</p><button type="button" data-testid="voice-stop" onClick={()=>void recording.current?.stop()}>Stop recording</button></>}
 {preview&&<><audio controls src={preview}/><button type="button" data-testid="voice-send" disabled={!available||busy||disabled} onClick={()=>void send()}>Send recording</button><p>The recording is sent only when you press Send recording.</p></>}
 {phase==='sending'&&<RequestStatus phase="transcribing"/>}
 {answer&&onUse&&<VoiceReview key={reviewVersion} answer={answer} onUse={onUse} disabled={busy||disabled}/>}
 {error&&<p role="alert"><Verbatim text={t(error)}/></p>}
 </section></Localize>;
}
