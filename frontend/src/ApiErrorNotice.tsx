import {useEffect,useRef} from 'react';
import {ApiError,friendlyApiError,isTemporaryApiError,serverBusyMessage} from './api.js';
import {Localize} from './i18n.js';
import {Verbatim} from './ModelHeadline.js';

export function ApiErrorNotice({error,onRetry,disabled=false,testId}:{error:unknown;onRetry?:()=>void;disabled?:boolean;testId?:string}){
 const box=useRef<HTMLDivElement>(null),temporary=isTemporaryApiError(error);
 useEffect(()=>{if(error&&!disabled)box.current?.focus()},[error,disabled]);
 if(!error)return null;
 return <Localize><div ref={box} tabIndex={-1} role="alert" data-testid={testId} className="api-error-notice">
  <p>{temporary?serverBusyMessage:error instanceof ApiError&&error.message.trim()?<Verbatim text={friendlyApiError(error)}/>:friendlyApiError(error)}</p>
  {temporary&&onRetry&&<button type="button" data-testid="api-retry" disabled={disabled} onClick={onRetry}>Try again</button>}
 </div></Localize>;
}
