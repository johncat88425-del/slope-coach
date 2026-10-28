import {useEffect,useState} from 'react';
export const demoSteps=[
 {route:'home',target:'[aria-label="Tool scope"]',text:'See the supported motion models and the limits of this check.'},
 {route:'audit',target:'[data-testid="interview-panel"]',text:'Upload a clip to answer capture questions; Muse Spark is credited only when the returned source is model, otherwise fixed questions are labeled mock.'},
 {route:'demo',target:'[data-testid="ghost-review"]',text:'Inspect saved SYNTHETIC results and compare backend ghost positions with recorded observations; this step makes no model call.'},
 {route:'demo',target:'[data-testid="physics-card"]',text:'Download an evidence card with assumptions and limitations; the Muse Spark headline remains pending until validated text is available.'},
 {route:'demo',target:'[data-testid="demo-comparison"]',text:'Compare consistent, inconsistent and insufficient-data outcomes together, using the same rules and clearly labeled SYNTHETIC examples.'},
] as const;
export function GuidedDemo({route}:{route:string}){
 const [step,setStep]=useState<number|null>(null);
 useEffect(()=>{if(step===null)return;const s=demoSteps[step];if(route!==s.route){location.hash=s.route;return}const target=document.querySelector<HTMLElement>(s.target);if(target instanceof HTMLDetailsElement)target.open=true;target?.scrollIntoView({block:'center',behavior:'smooth'});},[step,route]);
 return <aside className="guided-demo" aria-label="Guided demo" data-testid="guided-demo">{step===null?<button onClick={()=>setStep(0)}>Guided demo</button>:<><p role="status">{step+1} / {demoSteps.length} · {demoSteps[step].text}</p><button disabled={step===0} onClick={()=>setStep(s=>s===null?0:Math.max(0,s-1))}>Back</button><button data-testid="guided-next" onClick={()=>setStep(s=>s===null||s===demoSteps.length-1?null:s+1)}>{step===demoSteps.length-1?'Finish':'Next'}</button><button onClick={()=>setStep(null)}>Exit demo</button></>}</aside>
}
