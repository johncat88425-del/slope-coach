import type {ObjectSuggestion} from './api.js';
import {Localize} from './i18n.js';
import {Verbatim} from './ModelHeadline.js';
import {vehicleClassReferences} from './vehiclePresentation.js';
import type {VehicleClass} from './vehiclePresentation.js';

// A refreshed suggestion must never replace a name the user has edited.
export function suggestedObjectName(current:string,edited:boolean,suggestion?:ObjectSuggestion|null){
 return edited?current:suggestion?.object_name??current;
}
/** Suggest only semantic fields; measurements, capture conditions and confirmation stay with the user. */
export function suggestedVehicleFields(current:{model:string;vehicleClass:VehicleClass|''},edited:{model:boolean;vehicleClass:boolean},suggestion?:ObjectSuggestion|null){
 if(suggestion?.assumed_model!=='vehicle')return current;
 const model=edited.model?current.model:'vehicle';
 const vehicleClass=model==='vehicle'&&!edited.vehicleClass&&vehicleClassReferences.some(row=>row.value===suggestion.vehicle_class)?suggestion.vehicle_class!:current.vehicleClass;
 return {model,vehicleClass};
}
export function ObjectSuggestionHint({suggestion}:{suggestion?:ObjectSuggestion|null}){
 if(!suggestion)return null;
 return <Localize><div data-testid="object-suggestion"><p>Suggested by Muse Spark — please check</p>
 {suggestion.camera_looks_static===true&&<p>Muse Spark suggests the camera looks fixed. Please confirm it below.</p>}
 {suggestion.camera_looks_static===false&&<p>Muse Spark suggests the camera may be moving. Please check it below.</p>}
 {suggestion.judgeable===false?<p className="precheck-warning" role="status" data-testid="spark-precheck"><span>{suggestion.reason?'Muse Spark thinks this clip may not be judgeable:':'Muse Spark thinks this clip may not be judgeable.'}</span>{suggestion.reason&&<> <Verbatim text={suggestion.reason}/></>}</p>:suggestion.reason&&<p><Verbatim text={suggestion.reason}/></p>}
 </div></Localize>;
}
