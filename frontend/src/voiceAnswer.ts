import type {InterviewField,VoiceAnswer} from './api.js';

export const voiceFieldLabels:Record<InterviewField,string>={
 camera_static:'Camera remained fixed',slow_motion:'Slow motion or retimed playback',
 object_size_m:'Measured object size (metres)',length_m:'Pendulum length (metres)',
 assumed_model:'Motion model',time_window:'Time window (seconds)',
};
export type VoiceFormPatch=Partial<Record<'camera'|'slow'|'size'|'length'|'model'|'start'|'end',string>>;
export function voiceFieldPatch(field:InterviewField,value:unknown):VoiceFormPatch|null{
 if((field==='camera_static'||field==='slow_motion')&&typeof value==='boolean')return {[field==='camera_static'?'camera':'slow']:value?'yes':'no'};
 if((field==='object_size_m'||field==='length_m')&&typeof value==='number'&&Number.isFinite(value)&&value>0&&value<=100)return {[field==='object_size_m'?'size':'length']:String(value)};
 if(field==='assumed_model'&&['free_flight','bounce','pendulum','vehicle'].includes(value as string))return {model:value as string};
 if(field==='time_window'&&Array.isArray(value)&&value.length===2&&value.every(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0)&&value[0]<value[1])return {start:String(value[0]),end:String(value[1])};
 return null;
}
export function parseVoiceAnswer(raw:unknown):VoiceAnswer{
 const data=raw as VoiceAnswer;
 if(!data||typeof data!=='object'||typeof data.transcript!=='string'||typeof data.source?.transcript!=='string'||typeof data.source?.fields!=='string'||!data.fields||typeof data.fields!=='object'||Array.isArray(data.fields))throw new Error('The backend returned an unreadable voice answer. Please use the form fields.');
 const fields:VoiceAnswer['fields']={};
 if(data.source.fields!=='mock')for(const field of Object.keys(voiceFieldLabels) as InterviewField[]){
  const entry=data.fields[field];
  if(!entry)continue;
  if(entry.confirmed!==false||!voiceFieldPatch(field,entry.value))throw new Error('The backend returned an unreadable voice answer. Please use the form fields.');
  fields[field]=entry;
 }
 return {...data,fields};
}
export function voiceAudioFile(blob:Blob){
 const mime=blob.type.split(';')[0];
 const ext=mime==='audio/mp4'?'m4a':mime==='audio/ogg'?'ogg':mime==='audio/wav'?'wav':'webm';
 return new File([blob],'answer.'+ext,{type:blob.type});
}
