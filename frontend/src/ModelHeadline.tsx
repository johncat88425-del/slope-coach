import type {AuditOut} from './audit.js';
import {Localize} from './i18n.js';
/** Backend-validated content stays outside recursive UI translation. */
export function Verbatim({text}:{text:string}){return <>{text}</>}
export function ModelHeadline({headline}:{headline:AuditOut['headline']}){return headline?<header className="model-headline" data-testid="model-headline"><h2><Verbatim text={headline.text}/></h2><Localize><span>Written by Muse Spark</span></Localize></header>:null}
