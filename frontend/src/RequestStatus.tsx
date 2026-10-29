import {useEffect,useState} from 'react';
import {elapsedSeconds} from './requestFeedback.js';
import {Localize} from './i18n.js';
export type RequestPhase='scanning'|'checking'|'preparing'|'loading';
export function RequestStatus({phase}:{phase:RequestPhase}){const [seconds,setSeconds]=useState(0);useEffect(()=>{const start=performance.now();setSeconds(0);const timer=setInterval(()=>setSeconds(elapsedSeconds(start,performance.now())),250);return()=>clearInterval(timer)},[phase]);const labels={scanning:'Scanning the video…',checking:'Checking the motion…',preparing:'Preparing questions…',loading:'Loading the saved result…'};return <Localize><div data-testid="request-status" role="status"><p>{labels[phase]}</p><p aria-live="off">Elapsed: {seconds} seconds</p><p>This can take a little while. Your answers are kept; no automatic retry is made.</p></div></Localize>}
