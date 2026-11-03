/** User-selected coordinates in the preview media's native pixels; frame 0 is the selected window's first frame. */
export type TrackingPoint=[number,number,number];
export type FrameSize={width:number;height:number};
type Rect={left:number;top:number;width:number;height:number};
export function validFrameSize(size:FrameSize){return Number.isFinite(size.width)&&Number.isFinite(size.height)&&size.width>0&&size.height>0}
export function pointFromPointer(x:number,y:number,rect:Rect,size:FrameSize):TrackingPoint|undefined{
 if(!validFrameSize(size)||![x,y,rect.left,rect.top,rect.width,rect.height].every(Number.isFinite)||rect.width<=0||rect.height<=0)return;
 const scale=Math.min(rect.width/size.width,rect.height/size.height);
 const left=rect.left+(rect.width-size.width*scale)/2,top=rect.top+(rect.height-size.height*scale)/2;
 const px=(x-left)/scale,py=(y-top)/scale;
 if(px<0||py<0||px>size.width||py>size.height)return;
 return [Math.min(size.width-1,Math.round(px)),Math.min(size.height-1,Math.round(py)),0];
}
export function pointFromKey(key:string,current:TrackingPoint|undefined,size:FrameSize,fine=false):TrackingPoint|undefined{
 if(!validFrameSize(size)||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(key))return;
 const [x,y]=current??[Math.floor(size.width/2),Math.floor(size.height/2)];
 const step=fine?1:Math.max(1,Math.round(Math.min(size.width,size.height)/50));
 return [Math.max(0,Math.min(size.width-1,x+(key==='ArrowLeft'?-step:key==='ArrowRight'?step:0))),Math.max(0,Math.min(size.height-1,y+(key==='ArrowUp'?-step:key==='ArrowDown'?step:0))),0];
}
export function serializeTrackingPoint(point:TrackingPoint){
 if(!Array.isArray(point)||point.length!==3||!point.every(Number.isFinite)||point.some(v=>v<0)||!Number.isInteger(point[2]))throw new Error('Invalid tracking point. Clear it and select the object again.');
 return JSON.stringify(point);
}
