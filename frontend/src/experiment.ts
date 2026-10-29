export const pages = [
  {route: 'home', title: '首頁'},
  {route: 'setup', title: '場景設定'},
  {route: 'prediction', title: '預測'},
  {route: 'analysis', title: '影片分析'},
  {route: 'verification', title: '下一次驗證'},
  {route: 'report', title: '實驗報告'},
  {route: 'audit', title: '檢查影片'},
  {route:'demo',title:'對照展示'},
  {route:'wall',title:'結果牆'},
 {route:'compare',title:'雙片比較'},
 {route:'examples',title:'範例結果'},
 {route:'how',title:'運作方式'},
] as const;
export type Route = typeof pages[number]['route'];
export type Point = {x: number; y: number};
export type Media = {name: string; url: string};
export type Draft = {
  photo: Media | null;
  size: {width: number; height: number};
  points: Point[];
  length: string;
  height: string;
  rulerLength: string;
  captureConfirmed: boolean;
};
export type Calibration = {
  source: 'user_confirmed';
  imageSize: {width: number; height: number};
  points: Point[];
  lengthM: number;
  heightM: number;
  rulerLengthM: number;
};
export type Experiment = {
  id: string;
  draft: Draft;
  calibration: Calibration | null;
  video: Media | null;
  prediction: null;
  analysis: null;
  intervention: null;
};
export function createExperiment(id: string): Experiment {
  return {id, draft: {photo: null, size: {width: 0, height: 0}, points: [], length: '', height: '', rulerLength: '', captureConfirmed: false}, calibration: null, video: null, prediction: null, analysis: null, intervention: null};
}
export function auditIdFromHash(hash:string):string|null {
 const match=/^#\/audits\/([^/?#]+)$/.exec(hash);if(!match)return null;
 try {return decodeURIComponent(match[1]) || null} catch{return null}
}
export function auditHash(id:string){return '#/audits/'+encodeURIComponent(id)}
export function exampleKeyFromHash(hash:string){const m=/^#examples\/([^/?#]+)$/.exec(hash);try{return m?decodeURIComponent(m[1]):null}catch{return null}}
export function resolveRoute(hash: string): Route {
 if(exampleKeyFromHash(hash))return 'examples';
  if(auditIdFromHash(hash)!==null)return 'audit';
  const route = hash.replace(/^#\/?/, '');
  return pages.find(page => page.route === route)?.route ?? 'audit';
}
export function validateDraft(draft: Draft): string[] {
  const errors: string[] = [];
  if (!draft.photo) errors.push('請先上傳實驗照片。');
  if (!(draft.size.width > 0 && draft.size.height > 0)) errors.push('照片尚未成功載入，請重新選擇可讀取的圖片。');
  for (const [label, value] of [['沿面長度 L', draft.length], ['垂直高度 h', draft.height], ['尺兩端距離', draft.rulerLength]]) {
    if (!value.trim() || !Number.isFinite(Number(value)) || Number(value) <= 0) errors.push(`${label}必須是大於零的有限數值，單位為米。`);
  }
  if (Number(draft.height) >= Number(draft.length) && draft.length.trim() && draft.height.trim()) errors.push('垂直高度 h 必須小於沿面長度 L（不可 h ≥ L）。');
  if (draft.points.length !== 4) errors.push('請依序標記尺的兩端、滑塊（路徑起點）與坡底終點。');
  if (draft.points.some(p => !Number.isFinite(p.x) || !Number.isFinite(p.y) || p.x < 0 || p.y < 0 || p.x > draft.size.width || p.y > draft.size.height)) errors.push('標記必須位於原始照片範圍內。');
  if (draft.points.length >= 2 && draft.points[0].x === draft.points[1].x && draft.points[0].y === draft.points[1].y) errors.push('尺的兩端不能重疊。');
  if (draft.points.length === 4 && draft.points[2].x === draft.points[3].x && draft.points[2].y === draft.points[3].y) errors.push('路徑起點與終點不能重疊。');
  if (!draft.captureConfirmed) errors.push('請確認固定鏡頭、近似側視與同一運動平面的拍攝條件。');
  return errors;
}
// Only convert screen coordinates to source-image pixels; physical conversion belongs to Python.
export function imagePoint(client: Point, rect: {left: number; top: number; width: number; height: number}, size: {width: number; height: number}): Point | null {
  if (rect.width <= 0 || rect.height <= 0 || size.width <= 0 || size.height <= 0) return null;
  const x = (client.x - rect.left) / rect.width * size.width;
  const y = (client.y - rect.top) / rect.height * size.height;
  return x >= 0 && x <= size.width && y >= 0 && y <= size.height ? {x, y} : null;
}
export function updateDraft(experiment: Experiment, patch: Partial<Draft>): Experiment {
  return {...experiment, draft: {...experiment.draft, ...patch}, calibration: null};
}
export function replacePhoto(experiment: Experiment, photo: Media): Experiment {
  return updateDraft(experiment, {photo, size: {width: 0, height: 0}, points: [], captureConfirmed: false});
}
export function saveCalibration(experiment: Experiment): Experiment {
  const draft = experiment.draft;
  if (validateDraft(draft).length) return experiment;
  return {...experiment, calibration: {
    source: 'user_confirmed', imageSize: {...draft.size}, points: draft.points.map(p => ({...p})),
    lengthM: Number(draft.length), heightM: Number(draft.height), rulerLengthM: Number(draft.rulerLength),
  }};
}

export function auditIdFromPath(path:string){const m=/^\/audit\/([^/]+)\/?$/.exec(path);try{return m?decodeURIComponent(m[1]):null}catch{return null}}
export function shareAuditUrl(id:string,origin:string){return new URL('/audit/'+encodeURIComponent(id),origin).href}
