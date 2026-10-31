import carBraking from '../../data/demo/synthetic_car_50kmh_braking.json?raw';
import carLaunch from '../../data/demo/synthetic_car_3g_launch.json?raw';
import normal from '../../data/demo/synthetic_toss_normal_g.json?raw';
import inconsistent from '../../data/demo/synthetic_toss_quarter_g.json?raw';
import refused from '../../data/demo/synthetic_toss_moving_camera.json?raw';
import {parseSavedAudit} from './audit.js';
import {demoRecords} from './DemoCatalog.js';
import {FinalDemo} from './FinalDemo.js';
const cases=[normal,inconsistent,refused,carBraking,carLaunch].map(parseSavedAudit);
export function DemoPage(){return <FinalDemo records={demoRecords} synthetic={cases}/>}
