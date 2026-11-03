import carBraking from '../../data/demo/synthetic_car_50kmh_braking.json?raw';
import carLaunch from '../../data/demo/synthetic_car_3g_launch.json?raw';
import movingCamera from '../../data/demo/synthetic_toss_moving_camera.json?raw';
import {parseSavedAudit} from './audit.js';
const files=import.meta.glob('../../data/demo/real_own_*.json',{eager:true,query:'?raw',import:'default'});
const generated=import.meta.glob('../../data/demo/generated_*.json',{eager:true,query:'?raw',import:'default'});
export const demoRecords=Object.entries({...files,...generated}).sort(([a],[b])=>a.localeCompare(b)).map(([path,text])=>({key:path.split('/').at(-1)!.replace('.json',''),audit:parseSavedAudit(text as string)}));

/** Program-drawn examples keep a separate catalog and their explicit synthetic label. */
/** T265: since the depth correction every saved SAM clip can be judged, so the 'cannot judge' entry point is a
 * program-drawn clip (labelled synthetic) filmed by a camera that moves over a plain background. */
export const refusedDemoRecords=[{key:'synthetic_toss_moving_camera',audit:parseSavedAudit(movingCamera)}];
export const carDemoRecords=[{key:'synthetic_car_50kmh_braking',audit:parseSavedAudit(carBraking)},{key:'synthetic_car_3g_launch',audit:parseSavedAudit(carLaunch)}];
