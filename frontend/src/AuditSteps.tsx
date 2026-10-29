import {Localize} from './i18n.js';
export type AuditStep=0|1|2|3;
export function AuditSteps({current}:{current:AuditStep}){
 return <Localize><ol className="audit-steps" aria-label="Check progress" data-testid="audit-steps">
  {['Upload','Confirm','Check','Result'].map((label,i)=><li key={label} aria-current={i===current?'step':undefined}><span aria-hidden="true">{String(i+1).padStart(2,'0')} / </span>{label}</li>)}
 </ol></Localize>;
}
