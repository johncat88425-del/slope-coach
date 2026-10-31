import type {createApi} from './api.js';
import {GuidedDemo} from './GuidedDemo.js';
import {SpendPanel} from './SpendPanel.js';
import {Localize,LanguageSwitch} from './i18n.js';
export function SiteHeader({route}:{api:ReturnType<typeof createApi>;route:string}){
 return <Localize><a className="skip-link" href="#workspace">Skip to workspace</a><header className="site-header">
 <a className="wordmark" href="#home"><span className="brand-symbol" aria-hidden="true">↘</span>VIDEO PHYSICS AUDIT</a>
 <nav className="site-navigation" aria-label="Main sections"><a data-testid="nav-wall" href="#wall" aria-current={route==='wall'?'page':undefined}>Results</a><a href="#how" aria-current={route==='how'?'page':undefined}>How it works</a></nav><LanguageSwitch/>
 </header></Localize>;
}
export function SiteFooter({api,route}:{api:ReturnType<typeof createApi>;route:string}){return <Localize><footer className="site-footer"><p>Checks motion against a model.</p><nav className="utility-navigation" aria-label="Review resources"><a data-testid="nav-home" href="#home">Scope and limitations</a><a data-testid="nav-audit" href="#audit">Check video</a><a data-testid="nav-demo" href="#demo">Compare outcomes</a><a href="#compare">Compare two clips</a><a data-testid="nav-coach" href="#setup">Experiment coach</a></nav><div className="site-tools"><GuidedDemo route={route}/><SpendPanel api={api}/></div></footer></Localize>}
