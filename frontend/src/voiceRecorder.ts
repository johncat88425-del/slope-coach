export const MAX_VOICE_BYTES=10*1024*1024;
export type VoiceRecording={stop:()=>Promise<Blob>;cancel:()=>void;finished:Promise<Blob>};
export async function startVoiceRecording(options:{getStream?:()=>Promise<MediaStream>;makeRecorder?:(stream:MediaStream)=>MediaRecorder}={}):Promise<VoiceRecording>{
 const stream=await (options.getStream??(()=>navigator.mediaDevices.getUserMedia({audio:true})))();
 let released=false;
 const release=()=>{if(!released){released=true;stream.getTracks().forEach(track=>track.stop())}};
 try{
  const recorder=options.makeRecorder?options.makeRecorder(stream):new MediaRecorder(stream);
  const chunks:Blob[]=[];let size=0,settled=false,error:Error|undefined;
  let resolve!:(blob:Blob)=>void,reject!:(error:Error)=>void;
  const result=new Promise<Blob>((yes,no)=>{resolve=yes;reject=no});
  // Cancellation or a size limit can finish before the user presses Stop.
  void result.catch(()=>{});
  const finish=()=>{if(settled)return;settled=true;release();if(error)reject(error);else if(!size)reject(new Error('The recording is empty. Please try again.'));else resolve(new Blob(chunks,{type:recorder.mimeType||chunks[0]?.type||'audio/webm'}))};
  const stop=()=>{try{if(recorder.state!=='inactive')recorder.stop();else finish()}catch{error=new Error('The recording could not be finished. Please try again.');finish()}return result};
  recorder.ondataavailable=event=>{size+=event.data.size;if(size>MAX_VOICE_BYTES){error=new Error('The recording is larger than 10 MB. Please record a shorter answer.');void stop();return}if(event.data.size)chunks.push(event.data)};
  recorder.onstop=finish;
  recorder.onerror=()=>{error=new Error('The microphone recording failed. Please use the form fields.');void stop()};
  recorder.start(1000);
  return {stop,finished:result,cancel:()=>{error=new Error('Recording cancelled.');void stop();release()}};
 }catch(error){release();throw error}
}
