import {Localize,useTranslation} from './i18n.js';
import {useId,useRef,useState} from 'react';
import {windowKeyValue,canConfirmWithKey} from './windowKeyboard.js';
export function validWindow(start:string,end:string,duration:number){return start.trim()!==''&&end.trim()!==''&&Number.isFinite(Number(start))&&Number.isFinite(Number(end))&&Number(start)>=0&&Number(end)>Number(start)&&Number.isFinite(duration)&&duration>0&&Number(end)<=duration}
export function WindowSelector({url,start,end,confirmed,onChange,onConfirm,children}:{url:string;start:string;end:string;confirmed:boolean;onChange:(start:string,end:string)=>void;onConfirm:()=>void;children?:import('react').ReactNode}){
 const t=useTranslation(),helpId=useId();const video=useRef<HTMLVideoElement>(null);
 const [duration,setDuration]=useState(0),[error,setError]=useState('');const valid=validWindow(start,end,duration);
 function change(which:'start'|'end',value:string){onChange(which==='start'?value:start,which==='end'?value:end)}
 function confirm(){if(valid&&!confirmed)onConfirm()}
 return <Localize><section data-testid="window-selector" onKeyDown={e=>{if(e.target instanceof HTMLInputElement&&!e.nativeEvent.isComposing&&canConfirmWithKey(e.key,valid,confirmed)){e.preventDefault();confirm()}}}>
 <h3>Select and confirm a time window</h3>
 <video ref={video} controls src={url} onLoadedMetadata={e=>{setDuration(Number.isFinite(e.currentTarget.duration)?e.currentTarget.duration:0);setError('')}} onError={()=>setError('Cannot preview this video. Choose a supported video encoding.')}/>
 {error&&<p role="alert">{error}</p>}{children}
 <p id={helpId}>Arrow keys move a handle by 0.01 seconds. Home and End select the boundaries. Press Enter in a time field to confirm a valid window.</p>
 <div className="fields">{(['start','end'] as const).map(which=>{const value=which==='start'?start:end;return <div key={which}>
 <label>{which==='start'?'Start (seconds)':'End (seconds)'}<input data-testid={'window-'+which} type="number" aria-describedby={helpId} min="0" max={duration||undefined} step="0.01" value={value} onChange={e=>change(which,e.target.value)}/></label>
 <input aria-label={which==='start'?'Start handle':'End handle'} aria-describedby={helpId} aria-valuetext={`${Number(value||0).toFixed(2)} ${t('seconds')}`} type="range" min="0" max={duration||1} step="0.01" disabled={!duration} value={Math.min(duration||1,Math.max(0,Number(value||0)))} onKeyDown={e=>{const next=windowKeyValue(e.key,Number(value||0),duration);if(next!==null){e.preventDefault();change(which,next.toFixed(2))}}} onChange={e=>change(which,Number(e.target.value).toFixed(2))}/>
 <button disabled={!duration} onClick={()=>change(which,(video.current?.currentTime??0).toFixed(2))}>Use playback position</button>
 </div>})}</div>
 <p aria-live="polite">Selection: {start?Number(start).toFixed(2):'—'}–{end?Number(end).toFixed(2):'—'} s</p>
 <button data-testid="window-confirm" disabled={!valid||confirmed} onClick={confirm}>{confirmed?'Time window confirmed':'Confirm time window'}</button>
 <p>Changing either boundary requires confirmation again. No time is selected automatically.</p>
 </section></Localize>
}
