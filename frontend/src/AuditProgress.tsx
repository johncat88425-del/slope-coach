import {RequestStatus} from './RequestStatus.js';
import type {RequestPhase} from './RequestStatus.js';
import {Localize} from './i18n.js';
export function AuditProgress({percent,phase='checking'}:{percent:number|null;phase?:RequestPhase}){
 const uploading=typeof percent==='number'&&Number.isFinite(percent)&&percent>=0&&percent<100;
 return <Localize><div data-testid="audit-progress"><RequestStatus phase={uploading?'uploading':phase}/>{uploading&&<label>Upload progress<progress max="100" value={percent!}/>{percent}%</label>}<p>{percent===100?'Upload complete. Separate phase progress is not reported.':'The request is still running. Elapsed time is not a completion estimate.'}</p></div></Localize>;
}
