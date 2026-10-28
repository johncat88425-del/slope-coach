import {useEffect,useRef,useState} from 'react';
import type {createApi} from './api';
import type {AuditOut} from './audit';
import {validateAuditInput,verdictText} from './audit';
import {ModelSource} from './ModelSource';
import {Trajectory2D,TrajectoryOverlay} from './Trajectory';
import {mediaUrl} from './media';
export function AuditResult({audit}:{audit:AuditOut}){
 return <article aria-label="稽核結果"><h2>{verdictText(audit.verdict)}</h2><p>稽核 {audit.audit_id} · 假設：free_flight · 時間窗 {audit.t_start}–{audit.t_end} s</p><ModelSource source={audit.track_source} kind="tracking"/>
 <h3>原因</h3><ul>{audit.reasons.map((r,i)=><li key={i}>{r}</li>)}</ul>
 <h3>後端計算數字</h3>{Object.keys(audit.numbers).length?<dl>{Object.entries(audit.numbers).map(([key,value])=><div key={key}><dt>{key}</dt><dd>{String(value)}</dd></div>)}</dl>:<p>尚無可提供的數值。</p>}
 <TrajectoryOverlay url={mediaUrl(audit.overlay_url,import.meta.env?.VITE_API_BASE_URL)}/>
 <Trajectory2D points={audit.points.map(([t,x,y])=>({t,x,y}))}/>
 <h3>追蹤事件（需對照原片）</h3><ul>{audit.events.map((e,i)=><li key={i}>{e.t_s} s · {e.kind}：{e.detail}</li>)}</ul>
 <h3>已知限制</h3><ul>{audit.limits.map((r,i)=><li key={i}>{r}</li>)}</ul>
 </article>;
}
export function AuditPage({api}:{api:ReturnType<typeof createApi>}){
 const [file,setFile]=useState<File|null>(null),[preview,setPreview]=useState('');
 const [start,setStart]=useState(''),[end,setEnd]=useState(''),[size,setSize]=useState(''),[fixed,setFixed]=useState(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[attempted,setAttempted]=useState(false);
 const [audit,setAudit]=useState<AuditOut|null>(null),[id,setId]=useState('');
 const video=useRef<HTMLVideoElement>(null);const errors=validateAuditInput(start,end,size);
 useEffect(()=>()=>{if(preview)URL.revokeObjectURL(preview)},[preview]);
 async function run(action:()=>Promise<AuditOut>){if(busy)return;setBusy(true);setError('');try{const value=await action();setAudit(value);setId(value.audit_id)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 return <section aria-label="檢查影片"><h2>檢查影片</h2><p>檢查指定片段是否與自由落體模型一致。請先確認攝影條件與時間窗；缺少足夠觀測時會保留無法判斷的結果。</p>
 <fieldset disabled={busy}><legend>使用者確認的設定</legend><label>上傳影片<input type="file" accept="video/*" onChange={e=>{const f=e.target.files?.[0];if(f){setFile(f);setPreview(URL.createObjectURL(f));setAudit(null);setAttempted(false)}}}/></label>
 {(preview||audit?.video_url)&&<video ref={video} controls src={preview||mediaUrl(audit?.video_url,import.meta.env?.VITE_API_BASE_URL)} onError={()=>setError('影片無法播放，請確認編碼或重新選擇原片。')}/>}
 <div className="fields"><label>片段開始（秒）<input type="number" min="0" step="any" value={start} onChange={e=>setStart(e.target.value)}/></label><label>片段結束（秒）<input type="number" min="0" step="any" value={end} onChange={e=>setEnd(e.target.value)}/></label></div>
 <button disabled={!preview} onClick={()=>{if(video.current)setStart(String(video.current.currentTime))}}>用播放位置設定開始</button><button disabled={!preview} onClick={()=>{if(video.current)setEnd(String(video.current.currentTime))}}>用播放位置設定結束</button>
 <label>物體尺寸（米，選填）<input type="number" min="0" step="any" value={size} onChange={e=>setSize(e.target.value)}/></label><p>尺寸由使用者量測；未知請留空，不從物體名稱猜測。</p>
 <label><input type="checkbox" checked={fixed} onChange={e=>setFixed(e.target.checked)}/> 我確認鏡頭固定</label><p>未勾選會將 camera_static=false 送至後端，由後端保留無法判斷結果。</p>
 <button onClick={()=>{setAttempted(true);if(!file||errors.length)return;void run(()=>api.audit(file,Number(start),Number(end),fixed,size.trim()?Number(size):undefined))}}>提交片段檢查</button>
 {attempted&&(!file||errors.length>0)&&<div role="alert">{!file&&<p>請先選擇影片。</p>}<ul>{errors.map(e=><li key={e}>{e}</li>)}</ul></div>}
 <label>讀取既有稽核 ID<input value={id} onChange={e=>setId(e.target.value)}/></label><button disabled={!id.trim()} onClick={()=>void run(()=>api.getAudit(id.trim()))}>讀取稽核</button>
 </fieldset><div aria-live="polite">{busy&&<p role="status">正在處理片段，請勿重複提交…</p>}{error&&<p role="alert">{error}</p>}</div>{audit&&<AuditResult audit={audit}/>}
 </section>;
}
