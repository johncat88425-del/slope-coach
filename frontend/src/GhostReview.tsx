import {useRef,useState} from 'react';
import type {AuditOut} from './audit.js';
import {maximumGhostGap,recordedPointAt} from './ghost.js';
import {Localize} from './i18n.js';
export function GhostReview({audit,url}:{audit:AuditOut;url?:string}){
 const video=useRef<HTMLVideoElement>(null);const [time,setTime]=useState(audit.t_start);const [height,setHeight]=useState(270);
 const ghost=audit.ghost_points??[],gap=maximumGhostGap(audit.points,ghost);
 const current=recordedPointAt(audit.points,time),expected=recordedPointAt(ghost,time);
 const chartHeight=Math.max(height,...audit.points.map(p=>p[2]+12),...ghost.map(p=>p[2]+12));
 function seek(t:number){if(video.current){video.current.pause();video.current.currentTime=t;setTime(t);video.current.scrollIntoView({block:'center',behavior:'smooth'})}}
 return <Localize><section data-testid="ghost-review" aria-label="Ghost comparison"><h3>Ghost comparison</h3><p>Dashed ghost: where the backend model places the object under 9.81 m/s². Solid orange circles: recorded observations. This comparison is a display aid, not a new verdict.</p>
 {url ? <><div className="video-overlay"><video data-testid="ghost-video" ref={video} controls src={url} onLoadedMetadata={e=>setHeight(480*e.currentTarget.videoHeight/e.currentTarget.videoWidth)} onTimeUpdate={e=>setTime(e.currentTarget.currentTime)} onSeeked={e=>setTime(e.currentTarget.currentTime)}/><svg viewBox={`0 0 480 ${height}`} aria-label="Current recorded and ghost positions">{expected&&<circle cx={expected[1]} cy={expected[2]} r="12" fill="#00bcd4" fillOpacity=".25" stroke="#007e91" strokeWidth="3" strokeDasharray="6 4"/>}{current&&<circle cx={current[1]} cy={current[2]} r="8" fill="none" stroke="#f28c28" strokeWidth="3"/>}</svg></div><label>Playback position (seconds)<input data-testid="ghost-scrubber" type="range" min={audit.t_start} max={audit.t_end} step="0.01" value={Math.min(audit.t_end,Math.max(audit.t_start,time))} onChange={e=>seek(Number(e.target.value))}/></label><p>{time} s</p></> : <p>Original video unavailable. Recorded trajectories remain available below.</p>}
 {ghost.length ? <><svg viewBox={`0 0 480 ${chartHeight}`} role="img" aria-label="Recorded points and dashed ghost trajectory">{ghost.map((p,i)=><circle key={'g'+i} cx={p[1]} cy={p[2]} r="6" fill="#00bcd4" fillOpacity=".2" stroke="#007e91" strokeDasharray="3 2"/>)}{audit.points.map((p,i)=><circle key={'o'+i} cx={p[1]} cy={p[2]} r="3" fill="#c26319"/>)}{gap&&<line x1={gap.observed[1]} y1={gap.observed[2]} x2={gap.ghost[1]} y2={gap.ghost[2]} stroke="currentColor" strokeDasharray="2 3"/>}</svg>{gap&&<p data-testid="ghost-gap">Maximum matched-point separation: {gap.pixels} px · {gap.t} s {url&&<button onClick={()=>seek(gap.t)}>Review largest gap</button>}</p>}</> : <p>No backend ghost trajectory is available. No trajectory is invented.</p>}
 <h3>Review an event</h3><p>Jump to a reported event and inspect the original footage. Events may reflect tracking problems.</p><ul>{audit.events.map((e,i)=><li key={i}><button data-testid="event-seek" disabled={!url} onClick={()=>seek(e.t_s)}>{e.t_s} s · {e.kind}</button> {e.detail}</li>)}</ul>
 </section></Localize>
}
