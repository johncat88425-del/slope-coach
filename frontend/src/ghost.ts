export type VideoPoint=[number,number,number];
/** Display-only pixel comparison. Match timestamps exactly; never fit or interpolate. */
export function maximumGhostGap(observed:VideoPoint[],ghost:VideoPoint[]){
 const byTime=new Map(observed.map(p=>[p[0],p]));let result:{t:number;pixels:number;observed:VideoPoint;ghost:VideoPoint}|null=null;
 for(const g of ghost){const p=byTime.get(g[0]);if(!p||![...p,...g].every(Number.isFinite))continue;const pixels=Math.hypot(g[1]-p[1],g[2]-p[2]);if(!result||pixels>result.pixels)result={t:g[0],pixels,observed:p,ghost:g}}return result;
}
export function recordedPointAt(points:VideoPoint[],time:number){let best:VideoPoint|null=null;for(const p of points)if(p.every(Number.isFinite)&&Math.abs(p[0]-time)<=0.05&&(!best||Math.abs(p[0]-time)<Math.abs(best[0]-time)))best=p;return best}
