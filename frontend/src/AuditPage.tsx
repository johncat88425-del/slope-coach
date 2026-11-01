import {TrackCheck,WhatWouldFit} from './MuseAuditOutputs.js';
import {EarthAssumption} from './EarthAssumption.js';
import type {VehicleClass} from './vehiclePresentation.js';
import {AuditDimensionField,VehicleMeasurements,VehicleClassField} from './VehicleModel.js';
import {AuditSteps,type AuditStep} from './AuditSteps.js';
import {createRequestGate} from './requestFeedback.js';
import {verdictLabel,motionLabel} from './verdictLabel.js';
import {createSelectedDraft} from './selectedDraft.js';
import {RetakeGuide} from './RetakeGuide.js';
import {ModelUsage} from './ModelUsage.js';
import {ModelHeadline,Verbatim} from './ModelHeadline.js';
import {DEMO_ONLY} from './mode.js';
import {DemoUploadNotice} from './DemoUploadNotice.js';
import {WindowSuggestions} from './WindowSuggestions.js';
import {WindowSelector} from './WindowSelector.js';
import {PrintReport} from './PrintReport.js';
import {AuditProgress} from './AuditProgress.js';
import {GravityRuler} from './GravityRuler.js';
import {InterviewPanel} from './InterviewPanel.js';
import {BounceChart} from './BounceChart.js';
import {formatNumber} from './formatNumber.js';
import {PhysicsCard,PhysicsCardDownload} from './PhysicsCard.js';
import {GhostReview} from './GhostReview.js';
import {auditHash,shareAuditUrl} from './experiment.js';
import { Localize } from './i18n.js';
import { useEffect, useId, useRef, useState } from 'react';
import {friendlyApiError,isTemporaryApiError} from './api.js';
import {ApiErrorNotice} from './ApiErrorNotice.js';
import type { createApi } from './api';
import type { AuditModel, AuditOut } from './audit.js';
import { parseSavedAudit, validateAuditInput, verdictText } from './audit.js';
import { ModelSource } from './ModelSource.js';
import { Trajectory2D, TrajectoryOverlay } from './Trajectory.js';
import { matchingAuditPreview, mediaUrl } from './media.js';
import { auditMarkdown, downloadText } from './auditReport.js';
export function EventTimeline({events}:{events:AuditOut['events']}) {
 const labels:Record<string,string>={vanished:'Disappearance',size_jump:'Size jump',position_jump:'Position jump'};
 return <Localize><section data-testid="audit-events" aria-label="Tracking event timeline"><h3>Tracking event timeline</h3><p>Events may reflect tracking or capture problems. Review the original clip; they do not establish a cause.</p>{events.length ? <ol className="event-timeline">{[...events].sort((a,b)=>a.t_s-b.t_s).map((e,i)=><li key={i}><strong>{e.t_s} s · {labels[e.kind]??e.kind}</strong><p>{e.detail}</p><small>{e.kind}</small></li>)}</ol> : <p>No tracking events were reported.</p>}</section></Localize>;
}
export function AuditResult({ audit, replay = false, videoUrl, interviewSource, autoFocus=false, sampleKind=null }: {
    audit: AuditOut; replay?: boolean; videoUrl?:string;interviewSource?:'model'|'mock'|null;autoFocus?:boolean;sampleKind?:'generated'|'synthetic'|null;
}) {
    const [copyStatus,setCopyStatus]=useState('');
    const result=useRef<HTMLElement>(null),verdictId=useId();
    useEffect(()=>{if(autoFocus)result.current?.focus()},[autoFocus]);
    return <Localize><div className="audit-result-group"><article ref={result} tabIndex={-1} data-testid="audit-result" aria-label="稽核結果" aria-labelledby={verdictId}>
 <div className={'verdict-banner verdict-'+audit.verdict}><h2 id={verdictId} data-testid="audit-verdict">{verdictLabel(audit.verdict,audit.assumed_model)}</h2></div>
 {sampleKind&&<p className="sample-result-source source-label" data-testid="sample-result-source">{sampleKind==='synthetic'?'Synthetic test clip':'Generated test clip'}</p>}
 <TrackCheck check={audit.track_check}/>
 <VehicleMeasurements audit={audit}/>
 <ModelHeadline headline={audit.headline}/>
 {audit.explanation&&<section data-testid="audit-explanation"><p>{audit.explanation.source==='model'?'由 Muse Spark 產生':'固定模板（未使用模型）'}</p><p><Verbatim text={audit.explanation.text}/></p></section>}
 <section data-testid="audit-reasons"><h3>原因</h3><ul>{audit.reasons.map((reason,i)=><li key={i}><Verbatim text={reason}/></li>)}</ul></section>
 <WhatWouldFit audit={audit}/>
 <RetakeGuide verdict={audit.verdict} reasons={audit.reasons} modelTips={audit.retake_tips}/>
 <EarthAssumption numbers={audit.numbers}/>
 <details data-testid="audit-details"><summary>Details</summary>
 {replay&&<p role="status">Saved result replay — no new analysis or model call.</p>}{audit.synthetic&&<p role="status">SYNTHETIC test example — program-drawn motion.</p>}
 <p>稽核 {audit.audit_id} · 假設：{motionLabel(audit.assumed_model)} · 時間窗 {audit.t_start}–{audit.t_end} s</p><ModelSource source={audit.track_source} kind="tracking"/>
 {!replay&&<p><a href={'/audit/'+encodeURIComponent(audit.audit_id)}>Open result link</a><button data-testid="copy-audit-link" onClick={async()=>{try{await navigator.clipboard.writeText(shareAuditUrl(audit.audit_id,location.origin));setCopyStatus('Link copied.')}catch{setCopyStatus('Could not copy. Use the result link.')}}}>Copy link</button><span role="status">{copyStatus}</span></p>}
 <p data-testid="audit-slow-answer">Slow motion or retimed playback (user): {audit.slow_motion===true?'Yes':audit.slow_motion===false?'No':'Not provided'}</p>
 {audit.slow_motion===true&&audit.verdict==='insufficient_data'&&<aside data-testid="audit-timing-limit"><h3>Reported limitations</h3>{audit.reasons.map((r,i)=><blockquote key={i}><Verbatim text={r}/></blockquote>)}</aside>}
 <ModelUsage audit={audit} interviewSource={interviewSource}/>{audit.assumed_model!=='vehicle'&&<GravityRuler numbers={audit.numbers}/>}<h3>量測數字</h3>{Object.keys(audit.numbers).length ? <dl>{Object.entries(audit.numbers).map(([key, value]) => <div key={key}><dt>{key}</dt><dd title={String(value)}>{formatNumber(value,key)}</dd></div>)}</dl> : <p>尚無可提供的數值。</p>}
 {!replay && <TrajectoryOverlay url={mediaUrl(audit.overlay_url, import.meta.env?.VITE_API_BASE_URL)}/>}
 <GhostReview audit={audit} url={replay ? undefined : videoUrl??mediaUrl(audit.video_url, import.meta.env?.VITE_API_BASE_URL)}/><Trajectory2D points={audit.points.map(([t, x, y]) => ({ t, x, y }))}/>
 {audit.assumed_model==='bounce'&&<BounceChart numbers={audit.numbers}/>}
 {audit.assumed_model==='bounce' && <p>Rebound ratios compare each rebound height with the preceding height. Backend values are shown unchanged above.</p>}<EventTimeline events={audit.events}/>
 {audit.verdict==='insufficient_data' && audit.numbers.size_trend!==undefined && <aside data-testid="audit-size-trend" aria-label="Size trend limitation"><h3>Size trend limitation</h3><p>size_trend: <span title={String(audit.numbers.size_trend)}>{formatNumber(audit.numbers.size_trend)}</span></p><p>A changing apparent size can make the 2D motion check unreliable. The backend rejects changes beyond its quality threshold. Review the backend reasons above; this value alone does not establish a cause.</p></aside>}
 <PrintReport audit={audit}/><PhysicsCard showDownload={false} audit={audit} overlay={replay?undefined:mediaUrl(audit.overlay_url,import.meta.env?.VITE_API_BASE_URL)}/><button data-testid="audit-export-json" onClick={() => downloadText(JSON.stringify(audit, null, 2), audit.audit_id + ".json", "application/json;charset=utf-8")}>Save audit JSON</button><button data-testid="audit-export-markdown" onClick={() => downloadText(auditMarkdown(audit), audit.audit_id + '.md')}>匯出稽核 Markdown</button><h3>已知限制</h3><ul>{audit.limits.map((r, i) => <li key={i}><Verbatim text={r}/></li>)}</ul>
 </details></article><div className="result-actions" data-testid="audit-result-actions"><PhysicsCardDownload audit={audit} overlay={replay?undefined:mediaUrl(audit.overlay_url,import.meta.env?.VITE_API_BASE_URL)} label="Download share card PNG"/></div></div></Localize>;
}

export function AuditPage({ api, auditId = null }: {
    api: ReturnType<typeof createApi>; auditId?: string|null;
}) {
    const requestGate=useRef(createRequestGate()),retryRequest=useRef<(()=>void)|null>(null);
    const [requestPhase,setRequestPhase]=useState<'checking'|'loading'>('checking');
    const selectedDraft=useRef(createSelectedDraft<File>());
    const [previewAuditId,setPreviewAuditId]=useState<string|null>(null);
    const [windowConfirmed,setWindowConfirmed]=useState(false);
    const [file, setFile] = useState<File | null>(null), [preview, setPreview] = useState('');
    const [start, setStart] = useState(''), [end, setEnd] = useState(''), [size, setSize] = useState(''), [length,setLength]=useState(''), [fixed, setFixed] = useState(false);
    const [busy, setBusy] = useState(false), [error, setError] = useState(''), [attempted, setAttempted] = useState(false);
    const [audit, setAudit] = useState<AuditOut | null>(null), [id, setId] = useState('');
    const [interviewSource,setInterviewSource]=useState<'model'|'mock'|null>(null);
    const [interviewBusy,setInterviewBusy]=useState(false);
    const [interviewStep,setInterviewStep]=useState<AuditStep>(0);
    const [uploadPercent,setUploadPercent]=useState<number|null>(null);
    const [replay, setReplay] = useState(false);
    const [slowMotion,setSlowMotion]=useState('');
    const [objectName,setObjectName]=useState('ball');
    const [sampleKind,setSampleKind]=useState<'generated'|'synthetic'|null>(null);
    const [model, setModel] = useState<AuditModel>('free_flight');
    const [vehicleClass,setVehicleClass]=useState<VehicleClass|''>('unknown');
    useEffect(()=>{
        retryRequest.current=null;if(!auditId){setBusy(false);return;}let cancelled=false;setRequestPhase('loading');setBusy(true);setError('');selectedDraft.current.clear();setAudit(null);setPreview('');setReplay(DEMO_ONLY);setInterviewSource(null);setSampleKind(null);setId(auditId);
        (DEMO_ONLY?import('./DemoCatalog.js').then(({demoRecords})=>{const found=demoRecords.find(r=>r.audit.audit_id===auditId||r.key===auditId);if(!found)throw new Error('Saved example not found in this demo.');return found.audit}):api.getAudit(auditId)).then(value=>{if(!cancelled)setAudit(value)}).catch(e=>{if(!cancelled){setError(friendlyApiError(e));if(isTemporaryApiError(e)&&!DEMO_ONLY)retryRequest.current=()=>void run(()=>api.getAudit(auditId))}}).finally(()=>{if(!cancelled)setBusy(false)});
        return ()=>{cancelled=true};
    },[api,auditId]);
    const video = useRef<HTMLVideoElement>(null);
    const errors = validateAuditInput(start, end, size);if(model==='pendulum'&&length.trim()&&(!Number.isFinite(Number(length))||Number(length)<=0))errors.push('Pendulum length must be positive and finite; leave blank if unknown.');
    useEffect(() => () => { if (preview)
        URL.revokeObjectURL(preview); }, [preview]);
    async function run(action: () => Promise<AuditOut>, allowLocalPreview=false) { await requestGate.current(async()=>{if (busy)
        return;retryRequest.current=null;setRequestPhase(allowLocalPreview?'checking':'loading');setPreviewAuditId(null); setBusy(true); setError('');setInterviewSource(null);setSampleKind(null);setAudit(null);setUploadPercent(null); try {
        const value = await action();
        setPreviewAuditId(allowLocalPreview?value.audit_id:null);setAudit(value);window.dispatchEvent(new Event('audit-completed'));
        setReplay(false);
        setId(value.audit_id);
    }
    catch (e) {
        setError(friendlyApiError(e));if(isTemporaryApiError(e))retryRequest.current=()=>void run(action,allowLocalPreview);
    }
    finally {
        setBusy(false);
    } }); }
    return <Localize>{<section className="audit-flow" data-stage={interviewStep===0?'upload':interviewStep===3?'result':'confirm'} aria-label="檢查影片">
 <AuditSteps current={interviewStep}/><div className="audit-intro"><p className="eyebrow">THE MOTION DESK</p><h1>{interviewStep===3?'The motion, reviewed.':interviewStep===2?'Checking the motion…':interviewStep===0?'Check the physics in your video.':'Set the conditions.'}</h1><p>Upload a clip. Confirm the conditions. Compare its motion with the model you choose.</p></div>
 {DEMO_ONLY?<DemoUploadNotice/>:<InterviewPanel api={api} hasResult={Boolean(audit)} onNewSource={()=>{setAudit(null);setSampleKind(null);setInterviewSource(null);setInterviewStep(0);setError('')}} onStepChange={setInterviewStep} disabled={busy} onBusyChange={setInterviewBusy} onResult={(value,source,kind)=>{selectedDraft.current.clear();window.dispatchEvent(new Event('audit-completed'));setInterviewSource(source??null);setSampleKind(kind??null);setAudit(value);setReplay(false);setId(value.audit_id);setPreview('');setFile(null);setError('')}}/>}
 <details className="audit-utility"><summary>Recording tips</summary><aside data-testid="capture-checklist"><h3>Before recording</h3><ul><li>Keep the camera fixed on a tripod.</li><li>Film from the side.</li><li>Keep one moving object in frame.</li><li>Use a clearly coloured ball, such as orange.</li><li>Use normal speed, without slow motion or retiming.</li><li>Keep motion parallel to the image plane, away from the camera direction.</li></ul><p>When capture conditions or evidence fail the quality checks, the system returns insufficient data rather than forcing an answer.</p></aside></details>
 <details className="audit-utility" data-testid="offline-import"><summary>Offline demo: import saved JSON</summary><fieldset disabled={busy||interviewBusy}><legend>Offline demo</legend><p>Load a previously saved result. No network connection or tracking is needed.</p><label>Saved audit JSON<input data-testid="audit-import-json" type="file" accept=".json,application/json" onChange={async e => { const saved = e.target.files?.[0]; if (!saved) return; setError(''); try { if(saved.size > 5 * 1024 * 1024) throw new Error('Saved JSON must be under 5 MB.'); const result = parseSavedAudit(await saved.text()); selectedDraft.current.clear();setAudit(result);setInterviewSource(null);setSampleKind(null); setReplay(true); setPreview(''); setFile(null); } catch(e) {setError(friendlyApiError(e));} }}/></label></fieldset></details>
 {!DEMO_ONLY&&<details className="audit-utility" data-testid="advanced-audit"><summary>Advanced: check without the interview</summary><fieldset disabled={busy||interviewBusy}><legend>使用者確認的設定</legend><label>Object name<input data-testid="audit-object-name" value={objectName} onChange={e=>setObjectName(e.target.value)}/></label><label>Slow motion or retimed playback<select data-testid="audit-slow-motion" value={slowMotion} onChange={e=>setSlowMotion(e.target.value)}><option value="">Not provided</option><option value="yes">Yes</option><option value="no">No</option></select></label><label>Motion model<select data-testid="audit-model" value={model} onChange={e=>setModel(e.target.value as AuditModel)}><option value="free_flight">Free flight</option><option value="bounce">Bounce</option><option value="pendulum">Pendulum</option><option value="vehicle">Car driving past side-on (fixed camera)</option></select></label><label>上傳影片<input data-testid="audit-video-input" type="file" accept="video/*" onChange={e => { const f = e.target.files?.[0]; if (f) {
        retryRequest.current=null;setError('');selectedDraft.current.select(f);setFile(f);setStart('');setEnd('');setWindowConfirmed(false);
        setPreview(URL.createObjectURL(f));
        setAudit(null);
        setAttempted(false);
    } }}/></label>
 {preview&&<WindowSelector key={preview} url={preview} start={start} end={end} confirmed={windowConfirmed} onChange={(s,e)=>{setStart(s);setEnd(e);setWindowConfirmed(false)}} onConfirm={()=>setWindowConfirmed(true)}><WindowSuggestions key={preview+objectName} api={api} objectName={objectName} prepare={()=>selectedDraft.current.prepare(async selected=>(await api.auditDraft(selected)).draft_id)} onSelect={(s,e)=>{setStart(s);setEnd(e);setWindowConfirmed(false)}}/></WindowSelector>}
 {model==='pendulum'&&<label>Pendulum length (metres, optional)<input data-testid="pendulum-length" type="number" min="0" step="any" value={length} onChange={e=>setLength(e.target.value)}/></label>}{model==='vehicle'&&<VehicleClassField value={vehicleClass} onChange={setVehicleClass}/>}<AuditDimensionField model={model} value={size} onChange={setSize}/>
 <label><input type="checkbox" checked={fixed} onChange={e => setFixed(e.target.checked)}/> 我確認鏡頭固定</label><p>未勾選會將 camera_static=false 送至後端，由後端保留無法判斷結果。</p>
 <button data-testid="audit-submit" disabled={!windowConfirmed} onClick={() => { setAttempted(true); if (!file || !windowConfirmed || errors.length)
        return; const savedDraft=selectedDraft.current.take();void run(() => savedDraft?api.auditFromDraft(savedDraft,{t_start:Number(start),t_end:Number(end),camera_static:fixed,slow_motion:slowMotion?slowMotion==='yes':undefined,assumed_model:model,vehicle_class:model==='vehicle'?(vehicleClass||'unknown'):undefined,object_name:objectName,object_size_m:size.trim()?Number(size):undefined,length_m:model==='pendulum'&&length.trim()?Number(length):undefined}):api.audit(file, Number(start), Number(end), fixed, size.trim() ? Number(size) : undefined, model, setUploadPercent, model==='pendulum'&&length.trim()?Number(length):undefined,objectName,slowMotion?slowMotion==='yes':undefined,model==='vehicle'?(vehicleClass||'unknown'):undefined),true); }}>提交片段檢查</button>
 {attempted && (!file || errors.length > 0) && <div role="alert">{!file && <p>請先選擇影片。</p>}<ul>{errors.map(e => <li key={e}>{e}</li>)}</ul></div>}
 <label>讀取既有稽核 ID<input data-testid="audit-id" value={id} onChange={e => setId(e.target.value)}/></label><button data-testid="audit-load" disabled={!id.trim()} onClick={() => void run(() => api.getAudit(id.trim()))}>讀取稽核</button>
 </fieldset></details>}<div aria-live="polite">{busy && <AuditProgress percent={uploadPercent} phase={requestPhase}/>}<ApiErrorNotice testId="audit-error" error={error} disabled={busy||interviewBusy} onRetry={retryRequest.current??undefined}/></div>{audit && <AuditResult sampleKind={sampleKind} autoFocus key={audit.audit_id} audit={audit} replay={replay} videoUrl={matchingAuditPreview(audit.audit_id,previewAuditId,preview)} interviewSource={interviewSource}/>}
 </section>}</Localize>;
}
