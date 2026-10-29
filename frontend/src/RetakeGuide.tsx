import {Localize} from './i18n.js';
import {Verbatim} from './ModelHeadline.js';
export const retakeRules=[
 {id:'camera',pattern:/camera is not static|camera.*mov|camera_static.*false/i,tip:'Use a tripod and keep the camera fixed for the whole clip.'},
 {id:'perspective',pattern:/towards.*camera|away.*camera|object size changes|perspective/i,tip:'Film from the side, with motion parallel to the image plane.'},
 {id:'timing',pattern:/slow motion|retim|timing is not real time/i,tip:'Record and export at normal speed, without slow motion or retiming.'},
 {id:'tracking',pattern:/tracked in only|too few|not enough|insufficient.*point|no .*track|missing.*observ|no usable/i,tip:'Keep one clearly coloured object visible against a simple background throughout the motion.'},
 {id:'window',pattern:/window|too short|duration|flight segment/i,tip:'Include the whole motion and confirm its start and end in the video preview.'}
] as const;
export function retakeTips(reasons:string[]){return retakeRules.filter(r=>reasons.some(reason=>r.pattern.test(reason)))}
export function RetakeGuide({verdict,reasons}:{verdict:string;reasons:string[]}){if(verdict!=='insufficient_data')return null;const tips=retakeTips(reasons);return <Localize><aside data-testid="retake-guide"><h3>How to record another attempt</h3><p>Fixed checklist guidance — no model used. These suggestions do not establish the cause.</p><ul>{tips.length?tips.map(t=><li key={t.id}>{t.tip}</li>):<li>Review the capture checklist and the original clip before recording again.</li>}</ul><details><summary>Reported reasons</summary>{reasons.map((r,i)=><p key={i}><Verbatim text={r}/></p>)}</details></aside></Localize>}
