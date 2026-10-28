import {useEffect, useRef, useState} from 'react';
import type {MouseEvent} from 'react';
import {createRoot} from 'react-dom/client';
import {createExperiment, imagePoint, pages, replacePhoto, resolveRoute, saveCalibration, updateDraft, validateDraft} from './experiment';
import type {Draft, Point} from './experiment';
import './style.css';

const markerNames = ['尺的第一端', '尺的第二端', '滑塊位置'];
function App() {
  const [route, setRoute] = useState(() => resolveRoute(location.hash));
  const [experiment, setExperiment] = useState(() => createExperiment(crypto.randomUUID()));
  const [attempted, setAttempted] = useState(false);
  const [mediaError, setMediaError] = useState('');
  const [manualPoint, setManualPoint] = useState({x: '', y: ''});
  const image = useRef<HTMLImageElement>(null);
  const {draft, calibration, video} = experiment;
  const photoUrl = draft.photo?.url;
  const videoUrl = video?.url;
  const errors = validateDraft(draft);
  const activePage = pages.find(page => page.route === route)!;

  useEffect(() => {
    const update = () => setRoute(resolveRoute(location.hash));
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);
  useEffect(() => () => {if (photoUrl) URL.revokeObjectURL(photoUrl)}, [photoUrl]);
  useEffect(() => () => {if (videoUrl) URL.revokeObjectURL(videoUrl)}, [videoUrl]);
  useEffect(() => {document.title = `${activePage.title} · Slope Coach`}, [activePage.title]);

  function change(patch: Partial<Draft>) {
    setExperiment(current => updateDraft(current, patch));
    setAttempted(false);
  }
  function addPoint(point: Point) {
    if (draft.points.length < 3) change({points: [...draft.points, point]});
  }
  function mark(event: MouseEvent<HTMLDivElement>) {
    if (!image.current) return;
    const point = imagePoint({x: event.clientX, y: event.clientY}, image.current.getBoundingClientRect(), draft.size);
    if (point) addPoint(point);
  }

  return <>
    <header><b>Slope Coach</b><span>真實實驗 · 先預測再核對</span><small>本機 mock · 未連接後端</small></header>
    <main>
      <aside>
        <p className="eyebrow">實驗工作區</p><h1>上傳你的實驗，<br/>逐步核對證據。</h1>
        <nav aria-label="實驗步驟">{pages.map((page, index) => <a key={page.route} href={`#${page.route}`} aria-current={route === page.route ? 'page' : undefined}><span>{index + 1}</span>{page.title}</a>)}</nav>
        <p>固定鏡頭 · 近似正側視<br/>單一直線斜坡 · 單一滑塊</p>
      </aside>
      <section aria-label={activePage.title}>
        <div className="notice">目前為 mock 模式。照片、影片與實驗紀錄只留在這個分頁，重新整理會清除。分析結果尚未取得；不會把本機預覽當成已分析的實驗。</div>
        <details className="record"><summary>共用實驗紀錄</summary>
          <dl><dt>本機紀錄 ID</dt><dd>{experiment.id}</dd><dt>照片</dt><dd>{draft.photo?.name ?? '尚未上傳'}</dd><dt>校準草稿</dt><dd>{calibration ? '已確認並保存' : '尚未保存／已修改，需重新確認'}</dd><dt>影片</dt><dd>{video?.name ?? '尚未選擇'}</dd></dl>
        </details>
        {route === 'setup' && <>
          <p className="eyebrow">01 / 場景設定</p><h2>確認你的實驗裝置</h2>
          <p>上傳自己拍的照片。尺與滑塊放在同一運動平面，拍到完整路徑，避免人臉入鏡。</p>
          <label className="upload">上傳實驗照片<input type="file" accept="image/*" onChange={event => {
            const file = event.target.files?.[0]; if (!file) return;
            if (!file.type.startsWith('image/')) {setMediaError('請選擇圖片檔案。'); return}
            setMediaError(''); setAttempted(false); setManualPoint({x: '', y: ''});
            setExperiment(current => replacePhoto(current, {name: file.name, url: URL.createObjectURL(file)}));
          }}/></label>
          {draft.photo && <>
            <h3>標記：{markerNames[draft.points.length] ?? '標記完成'}</h3>
            <p id="marker-help">依序點選尺的兩端、滑塊。數字為原始照片像素座標；也可在下方輸入座標新增標記。</p>
            <div className="photo" onClick={mark} aria-describedby="marker-help">
              <img ref={image} src={draft.photo.url} alt="使用者上傳、待校準的實驗照片" onLoad={event => {
                const size = {width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight};
                // Reentering the route must preserve the saved calibration.
                if (size.width !== draft.size.width || size.height !== draft.size.height) change({size});
              }} onError={() => {setMediaError('照片無法讀取，請重新選擇 JPEG、PNG 或其他瀏覽器支援的圖片。'); change({size: {width: 0, height: 0}, points: []})}}/>
              {draft.size.width > 0 && draft.points.map((point, index) => <span className="marker" key={index} style={{left: `${point.x / draft.size.width * 100}%`, top: `${point.y / draft.size.height * 100}%`}}>{index + 1}</span>)}
            </div>
            <p>原始照片：{draft.size.width} × {draft.size.height} px；標記 {draft.points.length}/3</p>
            <div className="fields">
              <label>標記 X（px）<input type="number" min="0" max={draft.size.width} value={manualPoint.x} onChange={e => setManualPoint({...manualPoint, x: e.target.value})}/></label>
              <label>標記 Y（px）<input type="number" min="0" max={draft.size.height} value={manualPoint.y} onChange={e => setManualPoint({...manualPoint, y: e.target.value})}/></label>
            </div>
            <button disabled={draft.points.length >= 3 || !manualPoint.x.trim() || !manualPoint.y.trim() || !imagePoint({x: Number(manualPoint.x), y: Number(manualPoint.y)}, {left: 0, top: 0, width: draft.size.width, height: draft.size.height}, draft.size)} onClick={() => {addPoint({x: Number(manualPoint.x), y: Number(manualPoint.y)}); setManualPoint({x: '', y: ''})}}>新增座標標記</button>
            <button disabled={!draft.points.length} onClick={() => change({points: draft.points.slice(0, -1)})}>撤銷上一個標記</button>
            <ol aria-label="已選標記">{draft.points.map((point, index) => <li key={index}>{markerNames[index]}：({point.x.toFixed(1)}, {point.y.toFixed(1)}) px</li>)}</ol>
          </>}
          <h3>使用者量測並確認的尺寸</h3>
          <div className="fields">{([
            ['length', '斜坡沿面長度 L（米）'], ['height', '斜坡垂直高度 h（米）'], ['rulerLength', '尺兩端實際距離（米）'],
          ] as const).map(([key, label]) => <label key={key}>{label}<input type="number" min="0" step="any" value={draft[key]} onChange={event => change({[key]: event.target.value})}/></label>)}</div>
          <p>以上尺寸來自你使用尺量測後的輸入。影像估計：尚無；不會自動補入尺寸。</p>
          <label><input type="checkbox" checked={draft.captureConfirmed} onChange={event => change({captureConfirmed: event.target.checked})}/> 我已確認固定鏡頭、近似側視，尺與滑塊在同一平面。</label>
          <div aria-live="polite">{attempted && errors.length > 0 && <div role="alert"><p>無法保存校準，請修正：</p><ul>{errors.map(error => <li key={error}>{error}</li>)}</ul></div>}
            {calibration && <p role="status">已保存本機校準草稿；後端校準與版本尚待確認。</p>}</div>
          <button className="primary" onClick={() => {setAttempted(true); setExperiment(current => saveCalibration(current))}}>保存校準草稿</button>
          {calibration && <a className="next" href="#prediction">繼續至預測 →</a>}
        </>}
        {route === 'prediction' && <>
          <p className="eyebrow">02 / 預測</p><h2>在實測之前保存預測</h2>
          <p>{calibration ? `使用者確認尺寸：L = ${calibration.lengthM} m，h = ${calibration.heightM} m。` : '請先回到場景設定，完成校準草稿。'}</p>
          <div className="empty"><Legend/><h3>尚無已鎖定的預測</h3><p>目前 mock 紀錄沒有基準試驗或預測資料。需先完成獨立基準試驗，由後端計算並保存預測，再提交測試影片。</p></div>
          <button disabled>鎖定預測（等待後端）</button>
        </>}
        {route === 'analysis' && <>
          <p className="eyebrow">03 / 影片分析</p><h2>上傳自己拍的實驗影片</h2>
          <p>目前可選擇並預覽真實影片。尚未鎖定預測，影片不會提交分析；串接後端後須先鎖定再上傳。</p>
          <label className="upload">選擇實驗影片（本機預覽）<input type="file" accept="video/*" onChange={event => {
            const file = event.target.files?.[0]; if (!file) return;
            if (!file.type.startsWith('video/')) {setMediaError('請選擇影片檔案。'); return}
            setMediaError(''); setExperiment(current => ({...current, video: {name: file.name, url: URL.createObjectURL(file)}}));
          }}/></label>
          {video && <><p>已選擇：{video.name}</p><video controls src={video.url} onError={() => setMediaError('影片無法播放，請使用瀏覽器支援的編碼重新匯出影片。')}/></>}
          <div className="empty"><Legend/><p>尚無可用追蹤資料，不產生曲線或測量數字。未來缺失區段將保留斷線。</p></div>
          <button disabled>提交並分析（等待後端與已鎖定預測）</button>
        </>}
        {route === 'verification' && <>
          <p className="eyebrow">04 / 下一次驗證</p><h2>依證據選下一次核對</h2><p>目前證據不足，尚無驗證建議。以下為允許的核對類型，並非本次分析結論。</p>
          <div className="empty"><h3>釋放方式核對</h3><p>保持坡度、表面和起點不變，以擋片避免向前推；須先有可信的起滑時間與量測。</p><h3>尺寸核對</h3><p>重測高度與沿面長度；先保存新版本預測，再重做試驗。</p></div><button disabled>取得建議（等待後端）</button>
        </>}
        {route === 'report' && <>
          <p className="eyebrow">05 / 實驗報告</p><h2>回看同一份實驗紀錄</h2>
          <dl><dt>照片</dt><dd>{draft.photo?.name ?? '未提供'}</dd><dt>校準</dt><dd>{calibration ? `使用者確認：L ${calibration.lengthM} m / h ${calibration.heightM} m / 尺距離 ${calibration.rulerLengthM} m` : '尚未保存有效草稿'}</dd><dt>影片</dt><dd>{video?.name ?? '未提供'}</dd><dt>影像估計／實測結果</dt><dd>尚未取得</dd><dt>預測與驗證紀錄</dt><dd>尚未建立</dd></dl>
          <button disabled>匯出報告（T13）</button>
        </>}
        {mediaError && <p role="alert">{mediaError}</p>}
        <footer><a href="#setup">返回場景設定</a><span>可隨時查看前一步，切頁不清除目前紀錄。</span></footer>
      </section>
    </main>
  </>;
}
function Legend() {
  return <div className="legend" aria-label="曲線圖例"><span><i className="prediction-line"/>預測（青色虛線）</span><span><i className="observed-line"/>實測（橘色實線）</span></div>;
}
createRoot(document.getElementById('root')!).render(<App/>);
