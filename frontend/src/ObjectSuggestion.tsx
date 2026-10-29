import type {ObjectSuggestion} from './api.js';
import {Localize} from './i18n.js';
import {Verbatim} from './ModelHeadline.js';

// A refreshed suggestion must never replace a name the user has edited.
export function suggestedObjectName(current:string,edited:boolean,suggestion?:ObjectSuggestion|null){
 return edited?current:suggestion?.object_name??current;
}
export function ObjectSuggestionHint({suggestion}:{suggestion?:ObjectSuggestion|null}){
 if(!suggestion)return null;
 return <Localize><div data-testid="object-suggestion"><p>Suggested by Muse Spark — please check</p>
 {suggestion.camera_looks_static===true&&<p>Muse Spark suggests the camera looks fixed. Please confirm it below.</p>}
 {suggestion.camera_looks_static===false&&<p>Muse Spark suggests the camera may be moving. Please check it below.</p>}
 {suggestion.reason&&<p><Verbatim text={suggestion.reason}/></p>}
 </div></Localize>;
}
