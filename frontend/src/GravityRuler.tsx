import {Localize} from './i18n.js';
import {formatNumber} from './formatNumber.js';
export const gravityBodies=[['Pluto',.62],['Moon',1.62],['Mars',3.71],['Earth',9.81],['Jupiter',24.79]] as const;
export function GravityRuler({numbers:n}:{numbers:Record<string,number>}){
 const g=n.g_apparent_m_s2;if(!Number.isFinite(g)||g<=0)return <Localize><p>No gravity estimate is available.</p></Localize>;
 const low=n.g_apparent_low,high=n.g_apparent_high,range=Number.isFinite(low)&&Number.isFinite(high)&&low>0&&high>=low;
 const min=Math.min(.4,g,range?low:g),max=Math.max(30,g,range?high:g),x=(v:number)=>35+(Math.log(v)-Math.log(min))/(Math.log(max)-Math.log(min))*530;
 return <Localize><figure data-testid="gravity-ruler"><figcaption>Gravity comparison (m/s²)</figcaption><svg viewBox="0 0 610 160" role="img" aria-label="Estimated gravity and its range compared with reference values"><line x1="35" y1="80" x2="565" y2="80" stroke="currentColor"/>{gravityBodies.map(([name,v])=><g key={name}><line x1={x(v)} x2={x(v)} y1="70" y2="90" stroke="currentColor"/><text x={x(v)} y="115" textAnchor="middle">{name}</text><text x={x(v)} y="135" textAnchor="middle">{v}</text></g>)}{range&&<line x1={x(low)} x2={x(high)} y1="55" y2="55" stroke="#007e91" strokeWidth="10"/>}<path d={`M${x(g)-7} 30L${x(g)+7} 30L${x(g)} 45Z`} fill="#c26319"/></svg><p>Estimated gravity: <span title={String(g)}>{formatNumber(g)}</span> m/s²{range&&<> · Size-error range: {formatNumber(low)}–{formatNumber(high)} m/s²</>}</p><p>Planet names are only references, not an explanation. The range shows how a size error could affect the estimate. Spacing is scaled to fit the range.</p></figure></Localize>
}
