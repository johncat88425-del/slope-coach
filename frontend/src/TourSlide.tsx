import type {AuditOut} from './audit.js';
import {AuditResult} from './AuditPage.js';
import {PhysicsCard} from './PhysicsCard.js';
import {ModelSource} from './ModelSource.js';
import {Localize} from './i18n.js';
export function TourGhost({audit}:{audit:AuditOut}){
 if(!audit.points.length||!audit.ghost_points?.length)return <Localize><p>Saved comparison paths unavailable.</p></Localize>;
 const path=(points:AuditOut['points'])=>points.map(point=>`${point[1]},${point[2]}`).join(' ');
 return <Localize><figure className="tour-ghost" data-testid="tour-ghost"><figcaption>Earth model — dashed · Tracked motion — solid</figcaption><div className="tour-ghost-frame"><img src={(import.meta.env?.BASE_URL??'/')+'images/motion-study.jpg'} alt="A frame from a Meta AI–generated test clip (meta_clip4)"/><svg viewBox="0 0 480 270" aria-hidden="true">{audit.ghost_points&&audit.ghost_points.length>0&&<polyline points={path(audit.ghost_points)} fill="none" stroke="var(--color-earth)" strokeWidth="2" strokeDasharray="6 4"/>}{audit.points.length>0&&<polyline points={path(audit.points)} fill="none" stroke="var(--color-observed)" strokeWidth="2"/>}</svg></div><p>Saved image coordinates; paths outside the frame are clipped. No new fit or model call.</p><ModelSource source={audit.track_source} kind="tracking"/></figure></Localize>;
}
export function TourSlide({audit,view}:{audit:AuditOut|undefined;view:'result'|'ghost'|'share'}){
 if(!audit)return <Localize><p role="alert">The saved result is unavailable.</p></Localize>;
 return <Localize><div className={'tour-slide tour-view-'+view}>{audit.synthetic&&<p className="source-label" data-testid="tour-synthetic">Synthetic test clip</p>}{view==='share'?<PhysicsCard audit={audit}/>:<div className={view==='ghost'?'tour-evidence-grid':''}><AuditResult audit={audit} replay/>{view==='ghost'&&<TourGhost audit={audit}/>}</div>}</div></Localize>;
}
