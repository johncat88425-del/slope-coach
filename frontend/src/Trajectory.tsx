export type TrackPoint={t:number;x:number|null;y:number|null;quality?:string;breakBefore?:boolean};
export function Trajectory2D({points,sourceWidth=480,connect=false}:{points:TrackPoint[];sourceWidth?:number;connect?:boolean}){
 const valid=points.filter(p=>p.x!==null&&p.y!==null&&Number.isFinite(p.x)&&Number.isFinite(p.y)&&(!p.quality||p.quality==='ok'));
 if(!valid.length)return <p>尚無可顯示的實測軌跡。</p>;
 const height=Math.max(270,...valid.map(p=>p.y!+15));let d='',gap=true;
 for(const p of points){if(p.x===null||p.y===null||!Number.isFinite(p.x)||!Number.isFinite(p.y)||(p.quality&&p.quality!=='ok')){gap=true;continue}d+=`${gap||p.breakBefore?'M':'L'}${p.x},${p.y} `;gap=false}
 return <figure><figcaption>2D 實測軌跡（原點左上；座標寬度 {sourceWidth} px，y 向下）</figcaption><svg role="img" aria-label="橘色實測軌跡；缺失與不可靠觀測不連線" viewBox={`0 0 ${sourceWidth} ${height}`}>
 {connect&&<path d={d} fill="none" stroke="#c26319" strokeWidth="2"/>}{valid.map((p,i)=><circle key={i} cx={p.x!} cy={p.y!} r="3" fill="#c26319"><title>{`${p.t} s · (${p.x}, ${p.y}) px`}</title></circle>)}
 </svg><p>{connect?'缺失與非 ok 區段保留斷線。':'此資料未附完整逐影格品質，僅顯示實測散點，不猜測缺失區段或補線。'}</p></figure>;
}
export function TrajectoryOverlay({url}:{url?:string}){
 return url?<figure><figcaption>後端產生的追蹤疊加圖；請核對點是否落在物體上。</figcaption><img className="track-overlay" src={url} alt="後端追蹤軌跡疊加於原始影片影格"/></figure>:<p>目前無可用的軌跡疊加圖。</p>;
}
