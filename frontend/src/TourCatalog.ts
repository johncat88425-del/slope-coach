import carBraking from '../../data/demo/synthetic_car_50kmh_braking.json?raw';
import carLaunch from '../../data/demo/synthetic_car_3g_launch.json?raw';
import {parseSavedAudit} from './audit.js';
import {demoRecords} from './DemoCatalog.js';
export const tourRecords=[...demoRecords,{key:'synthetic_car_50kmh_braking',audit:parseSavedAudit(carBraking)},{key:'synthetic_car_3g_launch',audit:parseSavedAudit(carLaunch)}];
