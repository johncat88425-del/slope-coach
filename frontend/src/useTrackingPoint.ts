import {useEffect,useState} from 'react';
import type {TrackingPoint} from './trackingPoint.js';
/** Invalidate immediately on a different source/window, including before effect cleanup. */
export function useTrackingPoint(url:string,start:string,end:string,confirmed:boolean){
 const key=JSON.stringify([url,start,end]);
 const [selection,setSelection]=useState<{key:string;point:TrackingPoint}|null>(null);
 useEffect(()=>{setSelection(null)},[key,confirmed]);
 const point=confirmed&&selection?.key===key?selection.point:undefined;
 return [point,(next:TrackingPoint|undefined)=>setSelection(next?{key,point:next}:null)] as const;
}
