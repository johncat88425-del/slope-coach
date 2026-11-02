import {parseSavedAudit} from './audit.js';
import type {AuditOut} from './audit.js';
import {shareAuditUrl} from './experiment.js';

export const sharedUrlLimit=30*1024;
const byteLimit=1024*1024,pointLimit=600;
const keys=['audit_id','created_at','track_check','retake_tips','what_would_fit','headline','explanation','object_name','vehicle_class','slow_motion','assumed_model','t_start','t_end','camera_static','object_size_m','generated_clip','source','real_clip','labels_by','synthetic','nearest_body','length_m','track_source','verdict','reasons','numbers','events','limits'] as const;
export type AuditShareLink={url:string;embedded:boolean;pathReduced:boolean};
export const invalidSharedResult='This shared result is invalid or too large. Ask for the saved JSON.';
export function sharedPayloadFromHash(hash:string){return hash.startsWith('#r=')?hash.slice(3):null}
function drawingPath(points:[number,number,number][]){
 // Keep original observations, including endpoints; never interpolate or recalculate measurements.
 const selected=points.length<=pointLimit?points:Array.from({length:pointLimit},(_,i)=>points[Math.floor(i*(points.length-1)/(pointLimit-1))]);
 return selected.map(p=>[p[0],p[1],p[2]] as [number,number,number]);
}
function shareableAudit(audit:AuditOut){
 return {...Object.fromEntries(keys.map(key=>[key,audit[key]])),video_url:'',overlay_url:null,points:drawingPath(audit.points),...(audit.ghost_points?{ghost_points:drawingPath(audit.ghost_points)}:{})} as AuditOut;
}
async function readLimited(stream:ReadableStream<Uint8Array>,limit:number){
 const reader=stream.getReader(),chunks:Uint8Array[]=[];let size=0;
 try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>limit){await reader.cancel();throw new Error(invalidSharedResult)}chunks.push(value)}}finally{reader.releaseLock()}
 const all=new Uint8Array(size);let offset=0;for(const chunk of chunks){all.set(chunk,offset);offset+=chunk.byteLength}return all;
}
function base64url(bytes:Uint8Array){let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);return btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
function unbase64url(text:string){
 if(!text||text.length>sharedUrlLimit||!/^[\w-]+$/.test(text)||text.length%4===1)throw new Error(invalidSharedResult);
 const binary=atob(text.replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(text.length/4)*4,'='));return Uint8Array.from(binary,c=>c.charCodeAt(0));
}
export async function buildAuditShareLink(audit:AuditOut,origin:string,basePath='/',limit=sharedUrlLimit):Promise<AuditShareLink>{
 const fallback={url:shareAuditUrl(audit.audit_id,origin),embedded:false,pathReduced:false};
 if(typeof CompressionStream==='undefined')return fallback;
 try{
  const record=shareableAudit(audit),pathReduced=audit.points.length>pointLimit||(audit.ghost_points?.length??0)>pointLimit;
  parseSavedAudit(JSON.stringify(record));
  const raw=JSON.stringify({v:1,audit:record,path_reduced:pathReduced});if(new TextEncoder().encode(raw).byteLength>byteLimit)return fallback;
  const bytes=await readLimited(new Blob([raw]).stream().pipeThrough(new CompressionStream('gzip')),sharedUrlLimit);
  const url=new URL(basePath,origin);url.search='';url.hash='r='+base64url(bytes);
  return url.href.length<=limit?{url:url.href,embedded:true,pathReduced}:fallback;
 }catch{return fallback}
}
export async function decodeSharedAudit(payload:string):Promise<{audit:AuditOut;pathReduced:boolean}>{
 if(typeof DecompressionStream==='undefined')throw new Error('Compressed result links are not supported in this browser.');
 try{
  const bytes=unbase64url(payload),raw=await readLimited(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')),byteLimit);
  const value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));
  if(value?.v!==1||typeof value.path_reduced!=='boolean')throw new Error(invalidSharedResult);
  const original=parseSavedAudit(JSON.stringify(value.audit)),audit=shareableAudit(original);
  return {audit,pathReduced:value.path_reduced||original.points.length>pointLimit||(original.ghost_points?.length??0)>pointLimit};
 }catch{throw new Error(invalidSharedResult)}
}
