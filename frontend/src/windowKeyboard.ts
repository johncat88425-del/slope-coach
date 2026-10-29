/** Display-time controls only; no measurement or physics inference. */
export function windowKeyValue(key:string,current:number,duration:number):number|null{
 if(!Number.isFinite(current)||!Number.isFinite(duration)||duration<=0)return null;
 const limit=Math.floor(duration*100+1e-8),value=Math.round(current*100);
 const next=key==='ArrowLeft'||key==='ArrowDown'?value-1:key==='ArrowRight'||key==='ArrowUp'?value+1:key==='Home'?0:key==='End'?limit:null;
 return next===null?null:Math.min(limit,Math.max(0,next))/100;
}
export function canConfirmWithKey(key:string,valid:boolean,confirmed:boolean){return key==='Enter'&&valid&&!confirmed}
