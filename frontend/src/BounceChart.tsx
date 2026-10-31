import {Localize} from './i18n.js';
import {formatNumber} from './formatNumber.js';
export function BounceChart({numbers}:{numbers:Record<string,number>}){
 const bars=Object.entries(numbers).filter(([k,v])=>/^rebound_ratio_[1-9]\d*$/.test(k)&&Number.isFinite(v)&&v>=0).sort((a,b)=>Number(a[0].split('_').at(-1))-Number(b[0].split('_').at(-1)));
 if(!bars.length)return <Localize><p>No backend rebound ratios are available.</p></Localize>;
 const max=Math.max(1.1,...bars.map(([,v])=>v)),y=(v:number)=>210-v/max*175,w=520/bars.length;
 return <Localize><figure data-testid="bounce-chart"><figcaption>Rebound height ratios</figcaption><svg role="img" aria-label="Rebound ratios with a reference line at one" viewBox="0 0 600 260"><line x1="45" y1={y(1)} x2="580" y2={y(1)} stroke="currentColor" strokeDasharray="6 4"/><text x="5" y={y(1)+4}>1.0</text>{bars.map(([key,v],i)=><g key={key}><rect x={50+i*w} y={y(v)} width={Math.max(2,w-12)} height={210-y(v)} fill="var(--color-observed, #c26319)"/><text x={50+i*w} y={y(v)-5}>{formatNumber(v,key)}</text><text x={50+i*w} y="235">{key.split('_').at(-1)}</text></g>)}</svg><p>A ratio above 1 means a higher rebound than the preceding one. The backend applies its tolerance before deciding consistency; the chart does not issue a separate verdict.</p><details><summary>Rebound ratio data</summary><dl>{bars.map(([k,v])=><div key={k}><dt>{k}</dt><dd title={String(v)}>{formatNumber(v,k)}</dd></div>)}</dl></details></figure></Localize>
}
