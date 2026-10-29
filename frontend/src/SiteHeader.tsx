import type {createApi} from './api.js';
import {GuidedDemo} from './GuidedDemo.js';
import {SpendPanel} from './SpendPanel.js';
import {Localize} from './i18n.js';
export function SiteHeader({api,route}:{api:ReturnType<typeof createApi>;route:string}){
 return <Localize><a className="skip-link" href="#workspace">Skip to workspace</a>
  <header className="site-header">
   <a className="wordmark" href="#audit">VIDEO PHYSICS AUDIT</a>
   <nav className="site-navigation" aria-label="Main sections">
    <a data-testid="nav-audit" href="#audit" aria-current={route==='audit'?'page':undefined}>Check video</a>
    <a data-testid="nav-wall" href="#wall" aria-current={route==='wall'?'page':undefined}>Results wall</a>
    <a href="#compare" aria-current={route==='compare'?'page':undefined}>Compare two clips</a>
    <a href="#how" aria-current={route==='how'?'page':undefined}>How it works</a>
   </nav>
   <div className="site-tools"><GuidedDemo route={route}/><SpendPanel api={api}/></div>
  </header>
  <nav className="utility-navigation" aria-label="Review resources">
   <a data-testid="nav-home" href="#home">Scope and limitations</a>
   <a data-testid="nav-demo" href="#demo">Compare outcomes</a>
   <a data-testid="nav-coach" href="#setup">Experiment coach</a>
  </nav>
 </Localize>;
}
