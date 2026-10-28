import {formatNumber} from './formatNumber.js';
import type {AuditOut} from './audit';

export function physicsCardLines(a:AuditOut){
 const lines=['SLOPE COACH · PHYSICS CARD',a.synthetic?'SYNTHETIC TEST EXAMPLE — program-drawn motion':'Video motion audit',`Audit: ${a.audit_id}`,`Model: ${a.assumed_model}`,`${a.verdict==='consistent'?'Consistent':a.verdict==='inconsistent'?'Inconsistent':'Insufficient data'} with the assumed ${a.assumed_model.replace('_','-')} model`,'Muse Spark headline: awaiting a validated explanation'];
 if(a.nearest_body)lines.push(`Nearest gravity analogy: ${a.nearest_body} (an analogy, not a verdict)`);
 const labels:Record<string,string>={g_vs_earth:'Apparent gravity / Earth gravity',implied_time_factor:'Implied time factor (model-dependent)',implied_object_size_m:'Implied object size under model assumptions (m)',period_s:'Observed period (s)',implied_length_m:'Implied pendulum length (m)',predicted_period_s:'Predicted period (s)'};
 for(const [key,label] of Object.entries(labels))if(a.numbers[key]!==undefined)lines.push(`${label}: ${formatNumber(a.numbers[key],key)}`);
 if(a.numbers.g_verdict_robust===0)lines.push('CAUTION: the gravity verdict changes within the backend size-error range. Check the measured size.');
 lines.push(`Tracking: ${{frame_diff:'frame comparison',sam:'SAM 3.1',manual:'manual observations'}[a.track_source]}`,'Backend reasons:',...a.reasons,'Known limitations:',...a.limits,'Model-relative result only. This card does not establish provenance or cause.');return lines;
}
export async function downloadPhysicsCard(a:AuditOut,overlay?:string){
 const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');if(!ctx)throw new Error('PNG export is unavailable in this browser.');
 ctx.font='24px system-ui';const lines:string[]=[];
 for(const paragraph of physicsCardLines(a)){let line='';for(const word of paragraph.split(/\s+/)){if(ctx.measureText(line+' '+word).width>800&&line){lines.push(line);line=word}else line+=(line?' ':'')+word}lines.push(line,'')}
 let thumbnail:HTMLImageElement|undefined;
 if(overlay){try{thumbnail=await new Promise<HTMLImageElement>((resolve,reject)=>{const img=new Image();img.crossOrigin='anonymous';const timer=setTimeout(()=>reject(new Error('Thumbnail timed out')),5000);img.onload=()=>{clearTimeout(timer);resolve(img)};img.onerror=()=>{clearTimeout(timer);reject(new Error('Thumbnail unavailable'))};img.src=overlay})}catch{lines.push('Tracking thumbnail unavailable. Inspect the original audit overlay.')}}
 canvas.width=900;canvas.height=120+lines.length*34+(thumbnail?320:0);ctx.fillStyle='#f3f5f1';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#213c3b';ctx.font='24px system-ui';let y=55;
 for(const line of lines){ctx.fillText(line,45,y);y+=34}
 if(thumbnail){const ratio=Math.min(810/thumbnail.width,300/thumbnail.height);ctx.drawImage(thumbnail,45,y,thumbnail.width*ratio,thumbnail.height*ratio)}
 const blob=await new Promise<Blob>((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error('PNG export failed.')),'image/png'));
 const href=URL.createObjectURL(blob),link=document.createElement('a');link.href=href;link.download=a.audit_id+'-physics.png';link.click();setTimeout(()=>URL.revokeObjectURL(href),1000);
}
