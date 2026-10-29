import {RequestStatus} from './RequestStatus.js';
import type {RequestPhase} from './RequestStatus.js';
import {Localize} from './i18n.js';
export function AuditProgress({percent,phase='checking'}:{percent:number|null;phase?:RequestPhase}){return <Localize><div data-testid="audit-progress"><RequestStatus phase={phase}/>{percent!==null&&percent<100?<label>Upload progress<progress max="100" value={percent}/>{percent}%</label>:<progress aria-label="Waiting for server response"/>}<p>{percent===100?'Upload complete. Separate phase progress is not reported.':'The request is still running. Elapsed time is not a completion estimate.'}</p></div></Localize>}
