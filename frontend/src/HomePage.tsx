import {Home} from './Home.js';
import {demoRecords} from './DemoCatalog.js';
export function HomePage(){return <Home example={demoRecords.find(r=>r.key==='generated_meta_clip4')?.audit}/>;}
