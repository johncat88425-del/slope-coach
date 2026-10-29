import type {AuditModel,AuditVerdict} from './audit';
export function motionLabel(model:AuditModel){return {free_flight:'free flight on Earth',bounce:'passive bouncing',pendulum:'pendulum motion'}[model]}
export function verdictLabel(verdict:AuditVerdict,model:AuditModel){
 if(verdict==='insufficient_data')return 'Cannot judge this clip';
 return `${verdict==='consistent'?'Consistent':'Inconsistent'} with ${motionLabel(model)}`;
}
