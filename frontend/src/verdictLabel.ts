import type {AuditModel,AuditVerdict} from './audit';
export function verdictLabel(verdict:AuditVerdict,model:AuditModel){
 if(verdict==='insufficient_data')return 'Cannot judge this clip';
 const names:Record<AuditModel,string>={free_flight:'free flight on Earth',bounce:'passive bouncing',pendulum:'pendulum motion'};
 return `${verdict==='consistent'?'Consistent':'Inconsistent'} with ${names[model]}`;
}
