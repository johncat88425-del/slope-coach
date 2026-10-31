import {useEffect,useId,useRef,useState} from 'react';
import {recordingSteps,moveTourStep,tourKeyDirection} from './tourSteps.js';
import {tourRecords} from './TourCatalog.js';
import {TourSlide} from './TourSlide.js';
import {Localize} from './i18n.js';
export function RecordingTour({onClose}:{onClose:()=>void}){
 const [step,setStep]=useState(0),dialog=useRef<HTMLDialogElement>(null),heading=useRef<HTMLHeadingElement>(null),body=useRef<HTMLDivElement>(null),titleId=useId();
 const selected=recordingSteps[step],audit=tourRecords.find(record=>record.key===selected.key)?.audit;
 useEffect(()=>{const element=dialog.current;if(!element)return;element.showModal();return()=>element.close()},[]);
 useEffect(()=>{body.current?.scrollTo({top:0});heading.current?.focus({preventScroll:true})},[step]);
 return <Localize><dialog className="recording-tour" data-testid="recording-tour" ref={dialog} aria-labelledby={titleId} aria-modal="true" onCancel={event=>{event.preventDefault();onClose()}} onKeyDown={event=>{
  if(event.defaultPrevented||event.repeat)return;const target=event.target instanceof HTMLElement?event.target.closest<HTMLElement>('input,textarea,select,video,audio,button,a,summary,[contenteditable]')??event.target:{};
  const direction=tourKeyDirection(event.key,target,event.altKey||event.ctrlKey||event.metaKey||event.shiftKey);if(direction){event.preventDefault();setStep(current=>moveTourStep(current,direction))}
 }}>
 <header className="tour-header"><p className="eyebrow">RECORDING TOUR</p><span className="demo-counter" data-testid="guided-counter" aria-live="polite" aria-atomic="true" aria-label="Tour progress">{step+1} / {recordingSteps.length}</span><button onClick={onClose}>Exit demo</button></header>
 <div className="tour-body" ref={body}><h2 id={titleId} ref={heading} tabIndex={-1}>{selected.title}</h2><p>{selected.text}</p><p className="tour-replay-note">Saved results only — no new model call. Private videos are not loaded.</p><TourSlide key={selected.key+selected.view} audit={audit} view={selected.view}/></div>
 <footer className="tour-controls"><p className="tour-key-help">Left / Right: change step · Space: next step</p><button onClick={()=>setStep(current=>moveTourStep(current,-1))} disabled={step===0}>Back</button><button data-testid="guided-next" className="primary" onClick={()=>step===recordingSteps.length-1?onClose():setStep(current=>moveTourStep(current,1))}>{step===recordingSteps.length-1?'Finish':'Next'}</button></footer>
 </dialog></Localize>;
}
