import {AnalysisStages} from './AnalysisStages.js';
import {useEffect,useRef,useState} from 'react';
import {elapsedSeconds} from './requestFeedback.js';
import {Localize} from './i18n.js';
export type RequestPhase='scanning'|'checking'|'preparing'|'loading'|'uploading'|'transcribing';
export function RequestStatus({phase}:{phase:RequestPhase}){const feedback=useRef<HTMLDivElement>(null);
 useEffect(()=>{if(document.activeElement===document.body)feedback.current?.focus()},[]);
 const [seconds,setSeconds]=useState(0);useEffect(()=>{const start=performance.now();setSeconds(0);const timer=setInterval(()=>setSeconds(elapsedSeconds(start,performance.now())),250);return()=>clearInterval(timer)},[]);const labels={transcribing:'Transcribing your answer…',uploading:'Uploading the video…',scanning:'Scanning the video…',checking:'Checking the motion…',preparing:'Preparing questions…',loading:'Loading the saved result…'};return <Localize><div ref={feedback} tabIndex={-1} className="request-feedback" data-testid="request-status" role="status"><p>{labels[phase]}</p>{phase==='checking'&&<AnalysisStages/>}<p aria-live="off">Elapsed: {seconds} seconds</p><p>This can take a little while. Your answers are kept; no automatic retry is made.</p></div></Localize>}
