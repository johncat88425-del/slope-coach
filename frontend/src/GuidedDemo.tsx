import {lazy,Suspense,useRef,useState} from 'react';
import {Localize} from './i18n.js';
export {demoSteps} from './tourSteps.js';
const RecordingTour=lazy(()=>import('./RecordingTour.js').then(module=>({default:module.RecordingTour})));
export function GuidedDemo({route:_route,recording=false}:{route:string;recording?:boolean}){
 const [open,setOpen]=useState(false),launch=useRef<HTMLButtonElement>(null);
 return <Localize><aside className="guided-demo" aria-label="Guided demo" data-testid={recording?'recording-launcher':'guided-demo'}><button ref={launch} onClick={()=>setOpen(true)}>{recording?'Recording tour':'Guided demo'}</button>{open&&<Suspense fallback={<Localize><p role="status">Loading saved tour…</p></Localize>}><RecordingTour onClose={()=>{setOpen(false);requestAnimationFrame(()=>launch.current?.focus())}}/></Suspense>}</aside></Localize>;
}
