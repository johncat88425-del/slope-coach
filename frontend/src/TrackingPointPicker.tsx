import {useId,useRef,useState} from 'react';
import {Localize} from './i18n.js';
import {pointFromKey,pointFromPointer,validFrameSize} from './trackingPoint.js';
import type {FrameSize,TrackingPoint} from './trackingPoint.js';

export function TrackingPointPicker({url,start,value,onChange}:{url:string;start:number;value?:TrackingPoint;onChange:(point:TrackingPoint|undefined)=>void}){
 const helpId=useId(),video=useRef<HTMLVideoElement>(null);
 const [size,setSize]=useState<FrameSize>({width:0,height:0}),[ready,setReady]=useState(false),[error,setError]=useState(false),[cursor,setCursor]=useState<TrackingPoint>();
 function reviewFrame(element:HTMLVideoElement){
  if(!element.seeking&&element.readyState>=2&&Math.abs(element.currentTime-start)<.001&&validFrameSize({width:element.videoWidth,height:element.videoHeight}))setReady(true);
 }
 function select(point:TrackingPoint|undefined){if(point){setCursor(point);onChange(point)}}
 function clear(){setCursor(undefined);onChange(undefined)}
 const center:TrackingPoint=[Math.floor(size.width/2),Math.floor(size.height/2),0];
 return <Localize><section className="tracking-point-picker" data-testid="tracking-point-picker">
  <h3>Choose the tracking object (optional)</h3>
  <p>First frame of your confirmed time window. Tap or click the object to mark it. Skip this to track by the object name.</p>
  <p id={helpId}>Keyboard: arrow keys move the cursor; Shift + arrow moves one pixel. Enter or Space selects. Delete clears.</p>
  <button type="button" className="tracking-point-frame" data-testid="tracking-point-frame" aria-label="Select tracking object in the first frame" aria-describedby={helpId} disabled={!ready||error}
   style={{maxWidth:validFrameSize(size)?360*size.width/size.height:undefined,aspectRatio:validFrameSize(size)?`${size.width} / ${size.height}`:'16 / 9'}}
   onFocus={()=>setCursor(current=>current??value??center)}
   onClick={e=>{if(!ready)return;select(e.detail===0?cursor??value??center:pointFromPointer(e.clientX,e.clientY,video.current!.getBoundingClientRect(),size))}}
   onKeyDown={e=>{if(!ready||e.nativeEvent.isComposing)return;const next=pointFromKey(e.key,cursor??value,size,e.shiftKey);if(next){e.preventDefault();setCursor(next)}else if(e.key==='Enter'||e.key===' '){e.preventDefault();select(cursor??value??center)}else if(e.key==='Delete'||e.key==='Backspace'||e.key==='Escape'){e.preventDefault();clear()}}}>
   <video ref={video} src={url} muted playsInline preload="auto" aria-hidden="true" tabIndex={-1}
    onLoadedMetadata={e=>{const element=e.currentTarget;element.pause();setSize({width:element.videoWidth,height:element.videoHeight});setReady(false);element.currentTime=start;reviewFrame(element)}}
    onLoadedData={e=>reviewFrame(e.currentTarget)} onSeeked={e=>reviewFrame(e.currentTarget)} onPlay={e=>e.currentTarget.pause()}
    onError={()=>{setError(true);setReady(false);clear()}}/>
   {ready&&<svg viewBox={`0 0 ${size.width} ${size.height}`} preserveAspectRatio="xMidYMid meet" aria-hidden="true">
    {value&&<circle className="tracking-point-marker is-selected" data-testid="tracking-point-marker" cx={value[0]} cy={value[1]} r={Math.max(size.width,size.height)*.02} vectorEffect="non-scaling-stroke"/>}
    {cursor&&(!value||cursor[0]!==value[0]||cursor[1]!==value[1])&&<circle className="tracking-point-marker" data-testid="tracking-point-cursor" cx={cursor[0]} cy={cursor[1]} r={Math.max(size.width,size.height)*.02} vectorEffect="non-scaling-stroke"/>}
   </svg>}
  </button>
  {error?<p role="status">The first frame is unavailable. You can still continue with the object name.</p>:!ready?<p role="status">Loading the first frame…</p>:null}
  <p role="status" data-testid="tracking-point-status">{value?'Tracking point selected.':'No tracking point selected; the object name will be used.'}</p>
  {cursor&&<p role="status"><span>Cursor position (native pixels):</span> {cursor[0]}, {cursor[1]}</p>}
  {value&&<button type="button" data-testid="tracking-point-clear" onClick={clear}>Clear tracking point</button>}
 </section></Localize>;
}
