import {verdictEnglish} from './audit.js';
import type {AuditOut} from './audit.js';
import {ModelSource} from './ModelSource.js';
import {Localize} from './i18n.js';
/** Saved image coordinates only. The graphic never fits or calculates motion. */
export function HomeMotion({audit}:{audit?:AuditOut}){
 const observed=audit?.points??[],earth=(audit?.ghost_points??[]).filter(p=>p[2]<=270);
 const path=(points:typeof observed)=>points.map(p=>`${p[1]},${p[2]}`).join(' ');
 const end=observed.at(-1);
 return <Localize><figure className="home-motion" data-testid="home-motion">
 <div className="motion-frame"><img src={(import.meta.env?.BASE_URL??'/')+'images/motion-study.jpg'} alt="A frame from a Meta AI–generated test clip (meta_clip4)"/>
 {observed.length>0&&<svg viewBox="0 0 480 270" aria-hidden="true"><polyline className="hero-earth" points={path(earth)}/><polyline className="hero-observed" pathLength="1" points={path(observed)}/>{end&&<circle className="hero-endpoint" cx={end[1]} cy={end[2]} r="5"/>}</svg>}
 <div className="motion-legend"><span><i className="earth-key"/>Earth model</span><span><i className="clip-key"/>This clip</span></div>
 <p className="motion-conclusion">{audit?(audit.verdict==='inconsistent'?"Doesn't match Earth gravity.":verdictEnglish(audit)):'Saved motion evidence unavailable.'}</p></div>
 <figcaption>Generated test clip · saved tracking and model paths {audit&&<ModelSource source={audit.track_source} kind="tracking"/>}</figcaption>
 </figure></Localize>;
}
