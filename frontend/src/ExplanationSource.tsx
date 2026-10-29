import type {AuditOut} from './audit.js';
import {Localize} from './i18n.js';
export function ExplanationSource({explanation}:{explanation:AuditOut['explanation']}){
 if(!explanation)return null;
 return <Localize><span className="source-label" data-testid="explanation-source">{explanation.source==='model'?'由 Muse Spark 產生':'固定模板（未使用模型）'}</span></Localize>;
}
