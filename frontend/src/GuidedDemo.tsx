import {Localize} from './i18n.js';
import {useEffect,useRef,useState} from 'react';
export const demoSteps=[
 {route:'home',target:'[aria-label="Tool scope"]',text:'See the supported motion models and the limits of this check.'},
 {route:'audit',target:'[data-testid="interview-panel"]',text:'Upload a clip to answer capture questions; Muse Spark is credited only when the returned source is model, otherwise fixed questions are labeled mock.'},
 {route:'demo',target:'[data-testid="recorded-demo"]',text:'Review all experiments filmed and annotated by john, using the final saved results. Private videos are withheld.'},
 {route:'demo',target:'[data-demo-key="generated_meta_clip4"] [data-testid="ghost-review"]',text:'Compare the saved expected positions with SAM-tracked positions. This replay makes no model call and does not change the saved result.'},
 {route:'demo',target:'[data-demo-key="generated_meta_clip4"] [data-testid="physics-card"]',text:'Download an evidence card with the saved headline, assumptions and limitations. Muse Spark is credited only for supplied model text.'},
 {route:'demo',target:'[data-testid="demo-comparison"]',text:'Compare all recorded and generated test results under the same rules, including insufficient evidence. SYNTHETIC development examples remain separate.'},
] as const;
export function GuidedDemo({route}:{route:string}){
 const [step,setStep]=useState<number|null>(null);
 const previousStep=useRef<number|null>(null);
 const panel=useRef<HTMLElement>(null),launchButton=useRef<HTMLButtonElement>(null),nextButton=useRef<HTMLButtonElement>(null);
 useEffect(()=>{
  if(step===null){if(previousStep.current!==null)launchButton.current?.focus();previousStep.current=null;return}
  const changedStep=previousStep.current!==step;previousStep.current=step;
  const s=demoSteps[step];
  if(route!==s.route){if(changedStep)location.hash=s.route;else {previousStep.current=null;setStep(null)}return}
  const reveal=()=>{
   const target=document.querySelector<HTMLElement>(s.target);if(!target)return false;
   for(let parent=target.parentElement;parent;parent=parent.parentElement){if(parent instanceof HTMLDetailsElement)parent.open=true}
   if(target instanceof HTMLDetailsElement)target.open=true;
   target.scrollIntoView({block:'start',behavior:'auto'});
   if(!panel.current?.contains(document.activeElement))nextButton.current?.focus({preventScroll:true});
   return true;
  };
  if(reveal())return;
  // Route content is lazy-loaded; reveal evidence only after its view mounts.
  const observer=new MutationObserver(()=>{if(reveal())observer.disconnect()});
  observer.observe(document.getElementById('workspace')??document.body,{childList:true,subtree:true});
  return()=>observer.disconnect();
 },[step,route]);
 return <Localize><aside ref={panel} className={'guided-demo'+(step===null?'':' is-active')} aria-label="Guided demo" data-testid="guided-demo">{step===null?<button ref={launchButton} onClick={()=>setStep(0)}>Guided demo</button>:<><p role="status">{step+1} / {demoSteps.length} · {demoSteps[step].text}</p><button disabled={step===0} onClick={()=>setStep(s=>s===null?0:Math.max(0,s-1))}>Back</button><button ref={nextButton} data-testid="guided-next" onClick={()=>setStep(s=>s===null||s===demoSteps.length-1?null:s+1)}>{step===demoSteps.length-1?'Finish':'Next'}</button><button onClick={()=>setStep(null)}>Exit demo</button></>}</aside></Localize>
}
