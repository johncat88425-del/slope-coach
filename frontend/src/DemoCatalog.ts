import {parseSavedAudit} from './audit.js';
const files=import.meta.glob('../../data/demo/real_own_*.json',{eager:true,query:'?raw',import:'default'});
const generated=import.meta.glob('../../data/demo/generated_*.json',{eager:true,query:'?raw',import:'default'});
export const demoRecords=Object.entries({...files,...generated}).sort(([a],[b])=>a.localeCompare(b)).map(([path,text])=>({key:path.split('/').at(-1)!.replace('.json',''),audit:parseSavedAudit(text as string)}));
