import {CarPreview} from './CarPreview.js';
import {ResultPreview} from './ResultPreview.js';
import {Localize} from './i18n.js';
import {demoRecords,carDemoRecords} from './DemoCatalog';
import {openingExampleKeys} from './demoSelection.js';
export const openingKeys=openingExampleKeys;
export function OpeningCards(){return <Localize><section data-testid="reviewer-opening" className="results-opening"><p className="eyebrow">THE RESULTS</p><h1 className="page-title">Three possible answers.</h1><p>Same checks. Different motion. Explore the evidence behind each result.</p><div className="opening-cards">{openingKeys.map(key=>{const a=demoRecords.find(r=>r.key===key)?.audit;return a?<ResultPreview key={key} audit={a} recordKey={key}/>:null})}<CarPreview records={carDemoRecords}/></div></section></Localize>}
export function SavedExample({name}:{name:string|null}){const a=[...demoRecords,...carDemoRecords].find(r=>r.key===name)?.audit;return a?<SavedResult audit={a} replay/>:<Localize><p role="alert">Saved example not found. Open the results wall to choose a record.</p></Localize>}
import {AuditResult as SavedResult} from './AuditPage';
