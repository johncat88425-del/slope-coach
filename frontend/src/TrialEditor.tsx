import { Localize } from './i18n.js';
import { useRef, useState } from 'react';
import type { MouseEvent } from 'react';
import type { createApi, Detection, Trial } from './api';
import { ApiError } from './api';
import { ModelSource, sourceLabel } from './ModelSource';
import { imagePoint } from './experiment';
type Props = {
    trial: Trial;
    videoUrl?: string;
    api: ReturnType<typeof createApi>;
    run: (action: () => Promise<void>) => Promise<void>;
    refresh: () => Promise<void>;
};
export function TrialEditor({ trial, videoUrl, api, run, refresh }: Props) {
    const video = useRef<HTMLVideoElement>(null);
    const [manual, setManual] = useState(false), [detections, setDetections] = useState<Detection[]>([]);
    const [t0, setT0] = useState(trial.t0_s === null ? '' : String(trial.t0_s));
    const [suggestion, setSuggestion] = useState('');
    const [saved, setSaved] = useState(false);
    function record(event: MouseEvent<HTMLDivElement>) {
        if (!manual || !video.current || !video.current.paused)
            return;
        const el = video.current;
        const rect = el.getBoundingClientRect();
        // object-fit: contain may letterbox. Map only the displayed video content.
        const scale = Math.min(rect.width / el.videoWidth, rect.height / el.videoHeight);
        const width = el.videoWidth * scale, height = el.videoHeight * scale;
        const p = imagePoint({ x: event.clientX, y: event.clientY }, { left: rect.left + (rect.width - width) / 2, top: rect.top + (rect.height - height) / 2, width, height }, { width: el.videoWidth, height: el.videoHeight });
        if (p) {
            setSaved(false);
            setDetections(old => [...old.filter(d => d.t_s !== el.currentTime), { t_s: el.currentTime, centroid_px: [p.x, p.y] as [
                        number,
                        number
                    ], source: 'manual' as const }].sort((a, b) => a.t_s - b.t_s));
        }
    }
    return <Localize>{<div className="empty"><h3>試驗 {trial.trial_id} · {trial.kind}</h3><p>校準 v{trial.calibration_version}；已確認起滑：{trial.t0_s ?? '尚無'} s；來源：<ModelSource source={trial.t0_source ?? 'unknown'}/>；手動影格：{trial.manual_frames}</p>
    {videoUrl ? <div onClick={record}><video ref={video} controls={!manual} src={videoUrl} onError={() => setSuggestion('影片無法載入。請確認後端媒體仍存在，或重新選擇原片恢復預覽。')}/></div> : <p>此紀錄沒有可讀取的影片網址，請重新選取原片恢復預覽。</p>}
    <button onClick={() => void run(async () => { try {
        await api.track(trial.trial_id);
        await refresh();
    }
    catch (error) {
        if (error instanceof ApiError && error.status === 501) {
            setManual(true);
            setSuggestion('自動追蹤尚未接通。請暫停影片，點選滑塊中心；可移動播放時間後繼續標記。');
        }
        else
            throw error;
    } })}>自動追蹤</button>
    <button onClick={() => { video.current?.pause(); setManual(!manual); }}>{manual ? '關閉手動點選' : '手動標記影格'}</button>
    {manual && <><p>手動資料會明確標為 manual，不代表 SAM 觀測。每個時間戳只留一個標記；開啟點選會暫停並隱藏播放控制；需換影格時先關閉手動點選，使用播放時間軸，再開啟點選。保存會取代這段試驗的全部偵測資料。</p>
      <button disabled={!videoUrl} onClick={() => { if (video.current) {
            const time = video.current.currentTime;
            setSaved(false);
            setDetections(old => [...old.filter(d => d.t_s !== time), { t_s: time, centroid_px: null, source: 'manual' as const }].sort((a, b) => a.t_s - b.t_s));
        } }}>目前影格標為缺失</button>
      <button disabled={!detections.length} onClick={() => { setSaved(false); setDetections(detections.slice(0, -1)); }}>撤銷最後一筆</button>
      <p>{detections.length} 筆待保存{saved ? '（已送至後端）' : ''}</p>
      <button disabled={!detections.length || saved} onClick={() => void run(async () => { await api.detections(trial.trial_id, detections); setSaved(true); await refresh(); })}>保存全部手動標記</button>
      <details><summary>座標與來源</summary><pre>{JSON.stringify(detections, null, 2)}</pre></details>
    </>}
    <div className="fields"><label>使用者確認的起滑時刻（秒）<input type="number" step="any" min="0" value={t0} onChange={e => setT0(e.target.value)}/></label></div>
    <button onClick={() => void run(async () => { const s = await api.releaseSuggestion(trial.trial_id); setSuggestion(`${sourceLabel(s.source)}：候選 ${s.candidate_t0_s ?? '尚無'} s。${s.reason}。需你確認，不會自動採用。`); })}>取得起滑建議</button>
    <button disabled={!t0.trim() || !Number.isFinite(Number(t0)) || Number(t0) < 0} onClick={() => void run(async () => { await api.release(trial.trial_id, Number(t0)); await refresh(); })}>確認起滑時刻</button>
    {suggestion && <p role="status">{suggestion}</p>}
    <details><summary>後端追蹤資料（{trial.samples.length} 筆）</summary><div className="table-wrap"><table><thead><tr><th>影片時間 s</th><th>沿面位置 m</th><th>品質</th><th>來源</th></tr></thead><tbody>{trial.samples.map((s, i) => <tr key={i}><td>{s.t_s}</td><td>{s.s_m ?? '缺失'}</td><td>{s.quality}</td><td><ModelSource source={s.source} kind="tracking"/></td></tr>)}</tbody></table></div></details>
  </div>}</Localize>;
}
