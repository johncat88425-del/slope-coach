import {useState} from 'react';
import type {Calibration,Comparison,Prediction,Trial} from './api';
import {overlayFrame} from './overlay';
export function VideoOverlay({url,prediction,trial,calibration,comparison}:{url?:string;prediction:Prediction;trial:Trial;calibration:Calibration;comparison:Comparison}){
 const [confirmed,setConfirmed]=useState(false),[time,setTime]=useState(0),[size,setSize]=useState({w:0,h:0});
 const frame=confirmed?overlayFrame(time,prediction,trial,calibration,comparison):null;
 if(!url)return <p>沒有原片，無法顯示預測位置疊加。</p>;
 return <section aria-label="影片預測疊加"><h3>影片預測疊加</h3><label><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/> 我已核對此影片與校準照片相同視角、尺度、起點與可信的起滑時刻</label><p>預設關閉。青色虛線框：事前預測；橘色實線圓：實測在已確認路徑上的投影，並非物體輪廓。只取相鄰記錄影格（相差不超過 0.05 秒），缺失時隱藏實測，不補點。</p>
 <div className="video-overlay"><video controls src={url} onLoadedMetadata={e=>setSize({w:e.currentTarget.videoWidth,h:e.currentTarget.videoHeight})} onTimeUpdate={e=>setTime(e.currentTarget.currentTime)} onSeeked={e=>setTime(e.currentTarget.currentTime)}/>
 {frame&&size.w>0&&<svg viewBox={`0 0 ${size.w} ${size.h}`} aria-label="預測與實測投影位置"><rect x={frame.predicted[0]-12} y={frame.predicted[1]-12} width="24" height="24" fill="none" stroke="#00bcd4" strokeWidth="3" strokeDasharray="6 4"/>{frame.observed&&<circle cx={frame.observed[0]} cy={frame.observed[1]} r="10" fill="none" stroke="#f28c28" strokeWidth="3"/>}</svg>}
 </div>{confirmed&&!frame&&<p>目前時間或校準／起滑條件不符合，隱藏疊加；預測到達終點後也停止顯示。</p>}</section>;
}
