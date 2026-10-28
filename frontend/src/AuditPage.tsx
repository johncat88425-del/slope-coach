import {BounceChart} from './BounceChart.js';
import {formatNumber} from './formatNumber.js';
import {PhysicsCard} from './PhysicsCard.js';
import {GhostReview} from './GhostReview.js';
import {auditHash} from './experiment.js';
import { Localize } from './i18n.js';
import { useEffect, useRef, useState } from 'react';
import {friendlyApiError} from './api.js';
import type { createApi } from './api';
import type { AuditModel, AuditOut } from './audit.js';
import { parseSavedAudit, validateAuditInput, verdictText } from './audit.js';
import { ModelSource } from './ModelSource.js';
import { Trajectory2D, TrajectoryOverlay } from './Trajectory.js';
import { mediaUrl } from './media.js';
import { auditMarkdown, downloadText } from './auditReport.js';
export function EventTimeline({events}:{events:AuditOut['events']}) {
 const labels:Record<string,string>={vanished:'Disappearance',size_jump:'Size jump',position_jump:'Position jump'};
 return <Localize><section data-testid="audit-events" aria-label="Tracking event timeline"><h3>Tracking event timeline</h3><p>Events may reflect tracking or capture problems. Review the original clip; they do not establish a cause.</p>{events.length ? <ol className="event-timeline">{[...events].sort((a,b)=>a.t_s-b.t_s).map((e,i)=><li key={i}><strong>{e.t_s} s · {labels[e.kind]??e.kind}</strong><p>{e.detail}</p><small>{e.kind}</small></li>)}</ol> : <p>No tracking events were reported.</p>}</section></Localize>;
}
export function AuditResult({ audit, replay = false, videoUrl }: {
    audit: AuditOut; replay?: boolean; videoUrl?:string;
}) {
    return <Localize>{<article data-testid="audit-result" aria-label="稽核結果">{replay && <p role="status">Saved result replay — no new analysis or model call.</p>}{audit.synthetic&&<p role="status">Synthetic development fixture — not real footage.</p>}<h2 data-testid="audit-verdict">{verdictText(audit.verdict,audit.assumed_model)}</h2><p>稽核 {audit.audit_id} · 假設：{audit.assumed_model} · 時間窗 {audit.t_start}–{audit.t_end} s</p><ModelSource source={audit.track_source} kind="tracking"/>
 {!replay && <p><a href={auditHash(audit.audit_id)}>Open result link</a></p>}<h3>原因</h3><ul>{audit.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
 <h3>後端計算數字</h3>{Object.keys(audit.numbers).length ? <dl>{Object.entries(audit.numbers).map(([key, value]) => <div key={key}><dt>{key}</dt><dd title={String(value)}>{formatNumber(value,key)}</dd></div>)}</dl> : <p>尚無可提供的數值。</p>}
 {!replay && <TrajectoryOverlay url={mediaUrl(audit.overlay_url, import.meta.env?.VITE_API_BASE_URL)}/>}
 <GhostReview audit={audit} url={replay ? undefined : videoUrl??mediaUrl(audit.video_url, import.meta.env?.VITE_API_BASE_URL)}/><Trajectory2D points={audit.points.map(([t, x, y]) => ({ t, x, y }))}/>
 {audit.assumed_model==='bounce'&&<BounceChart numbers={audit.numbers}/>}
 {audit.assumed_model==='bounce' && <p>Rebound ratios compare each rebound height with the preceding height. Backend values are shown unchanged above.</p>}<EventTimeline events={audit.events}/>
 {audit.verdict==='insufficient_data' && audit.numbers.size_trend!==undefined && <aside data-testid="audit-size-trend" aria-label="Size trend limitation"><h3>Size trend limitation</h3><p>size_trend: <span title={String(audit.numbers.size_trend)}>{formatNumber(audit.numbers.size_trend)}</span></p><p>A changing apparent size can make the 2D motion check unreliable. The backend rejects changes beyond its quality threshold. Review the backend reasons above; this value alone does not establish a cause.</p></aside>}
 <PhysicsCard audit={audit} overlay={replay?undefined:mediaUrl(audit.overlay_url,import.meta.env?.VITE_API_BASE_URL)}/><button data-testid="audit-export-json" onClick={() => downloadText(JSON.stringify(audit, null, 2), audit.audit_id + ".json", "application/json;charset=utf-8")}>Save audit JSON</button><button data-testid="audit-export-markdown" onClick={() => downloadText(auditMarkdown(audit), audit.audit_id + '.md')}>匯出稽核 Markdown</button><h3>已知限制</h3><ul>{audit.limits.map((r, i) => <li key={i}>{r}</li>)}</ul>
 </article>}</Localize>;
}
export function AuditPage({ api, auditId = null }: {
    api: ReturnType<typeof createApi>; auditId?: string|null;
}) {
    const [file, setFile] = useState<File | null>(null), [preview, setPreview] = useState('');
    const [start, setStart] = useState(''), [end, setEnd] = useState(''), [size, setSize] = useState(''), [length,setLength]=useState(''), [fixed, setFixed] = useState(false);
    const [busy, setBusy] = useState(false), [error, setError] = useState(''), [attempted, setAttempted] = useState(false);
    const [audit, setAudit] = useState<AuditOut | null>(null), [id, setId] = useState('');
    const [uploadPercent,setUploadPercent]=useState<number|null>(null);
    const [replay, setReplay] = useState(false);
    const [model, setModel] = useState<AuditModel>('free_flight');
    useEffect(()=>{
        if(!auditId){setBusy(false);return;}let cancelled=false;setBusy(true);setError('');setAudit(null);setPreview('');setReplay(false);setId(auditId);
        api.getAudit(auditId).then(value=>{if(!cancelled)setAudit(value)}).catch(e=>{if(!cancelled)setError(friendlyApiError(e))}).finally(()=>{if(!cancelled)setBusy(false)});
        return ()=>{cancelled=true};
    },[api,auditId]);
    const video = useRef<HTMLVideoElement>(null);
    const errors = validateAuditInput(start, end, size);if(model==='pendulum'&&length.trim()&&(!Number.isFinite(Number(length))||Number(length)<=0))errors.push('Pendulum length must be positive and finite; leave blank if unknown.');
    useEffect(() => () => { if (preview)
        URL.revokeObjectURL(preview); }, [preview]);
    async function run(action: () => Promise<AuditOut>) { if (busy)
        return; setBusy(true); setError('');setAudit(null);setUploadPercent(null); try {
        const value = await action();
        setAudit(value);
        setReplay(false);
        setId(value.audit_id);
    }
    catch (e) {
        setError(friendlyApiError(e));
    }
    finally {
        setBusy(false);
    } }
    return <Localize>{<section aria-label="檢查影片"><h2>檢查影片</h2><p>Check the selected segment against the chosen motion model. Confirm capture conditions and the time window; insufficient evidence remains an explicit outcome.</p>
 <fieldset disabled={busy}><legend>Offline demo</legend><p>Load a previously saved result. No network connection or tracking is needed.</p><label>Saved audit JSON<input data-testid="audit-import-json" type="file" accept=".json,application/json" onChange={async e => { const saved = e.target.files?.[0]; if (!saved) return; setError(''); try { if(saved.size > 5 * 1024 * 1024) throw new Error('Saved JSON must be under 5 MB.'); const result = parseSavedAudit(await saved.text()); setAudit(result); setReplay(true); setPreview(''); setFile(null); } catch(e) {setError(friendlyApiError(e));} }}/></label></fieldset>
 <fieldset disabled={busy}><legend>使用者確認的設定</legend><label>Motion model<select data-testid="audit-model" value={model} onChange={e=>setModel(e.target.value as AuditModel)}><option value="free_flight">Free flight</option><option value="bounce">Bounce</option><option value="pendulum">Pendulum</option></select></label><label>上傳影片<input data-testid="audit-video-input" type="file" accept="video/*" onChange={e => { const f = e.target.files?.[0]; if (f) {
        setFile(f);
        setPreview(URL.createObjectURL(f));
        setAudit(null);
        setAttempted(false);
    } }}/></label>
 {!audit && preview && <video ref={video} controls src={preview} onError={() => setError('影片無法播放，請確認編碼或重新選擇原片。')}/>}
 <div className="fields"><label>片段開始（秒）<input type="number" min="0" step="any" value={start} onChange={e => setStart(e.target.value)}/></label><label>片段結束（秒）<input type="number" min="0" step="any" value={end} onChange={e => setEnd(e.target.value)}/></label></div>
 <button disabled={!preview} onClick={() => { if (video.current)
        setStart(String(video.current.currentTime)); }}>用播放位置設定開始</button><button disabled={!preview} onClick={() => { if (video.current)
        setEnd(String(video.current.currentTime)); }}>用播放位置設定結束</button>
 {model==='pendulum'&&<label>Pendulum length (metres, optional)<input data-testid="pendulum-length" type="number" min="0" step="any" value={length} onChange={e=>setLength(e.target.value)}/></label>}<label>物體尺寸（米，選填）<input type="number" min="0" step="any" value={size} onChange={e => setSize(e.target.value)}/></label><p>尺寸由使用者量測；未知請留空，不從物體名稱猜測。</p>
 <label><input type="checkbox" checked={fixed} onChange={e => setFixed(e.target.checked)}/> 我確認鏡頭固定</label><p>未勾選會將 camera_static=false 送至後端，由後端保留無法判斷結果。</p>
 <button data-testid="audit-submit" onClick={() => { setAttempted(true); if (!file || errors.length)
        return; void run(() => api.audit(file, Number(start), Number(end), fixed, size.trim() ? Number(size) : undefined, model, setUploadPercent, model==='pendulum'&&length.trim()?Number(length):undefined)); }}>提交片段檢查</button>
 {attempted && (!file || errors.length > 0) && <div role="alert">{!file && <p>請先選擇影片。</p>}<ul>{errors.map(e => <li key={e}>{e}</li>)}</ul></div>}
 <label>讀取既有稽核 ID<input data-testid="audit-id" value={id} onChange={e => setId(e.target.value)}/></label><button data-testid="audit-load" disabled={!id.trim()} onClick={() => void run(() => api.getAudit(id.trim()))}>讀取稽核</button>
 </fieldset><div aria-live="polite">{busy && <div data-testid="audit-progress" role="status">{uploadPercent===100 ? <p>Upload complete. Waiting for backend analysis; analysis progress is unavailable.</p> : uploadPercent!==null ? <><label>Upload progress<progress max="100" value={uploadPercent}/></label><p>{uploadPercent}%</p></> : <p>Request in progress. Please wait; no automatic retry will be made.</p>}</div>}{error && <p data-testid="audit-error" role="alert">{error}</p>}</div>{audit && <AuditResult key={audit.audit_id} audit={audit} replay={replay} videoUrl={preview || undefined}/>}
 </section>}</Localize>;
}
