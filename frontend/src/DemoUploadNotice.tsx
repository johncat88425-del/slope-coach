import {Localize} from './i18n.js';

export function liveAppUrl(value?:string){
 if(!value?.trim())return null;
 try{const url=new URL(value.trim());return ['https:','http:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null}catch{return null}
}
export function DemoUploadNotice({liveUrl=import.meta.env?.VITE_LIVE_URL}:{liveUrl?:string}){
 const url=liveAppUrl(liveUrl);
 return <Localize><section className="demo-upload-notice" data-testid="demo-upload-notice" aria-label="Upload your own video">
  <h2>This page only replays saved results.</h2>
  {url?<a className="next primary" data-testid="open-live-app" href={url}>To upload your own video, open the live app →</a>:<>
   <p>The live app link is not available yet. Run the full app locally:</p>
   <pre><code>{'git clone https://github.com/johncat88425-del/slope-coach.git\ncd slope-coach\n./scripts/dev.sh'}</code></pre>
   <p><a href="https://github.com/johncat88425-del/slope-coach#installation--setup">Read the setup requirements in the README</a></p>
  </>}
  <p><a href="#wall">Explore saved examples →</a></p>
 </section></Localize>;
}
