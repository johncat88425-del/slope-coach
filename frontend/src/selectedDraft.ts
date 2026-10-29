export class StaleSelectionError extends Error {
 constructor(){super('The selected video changed. Request suggestions again.');this.name='StaleSelectionError'}
}
/** Bind an async draft to one explicit user selection; late results never cross selections. */
export function createSelectedDraft<T>(){
 let selection:T|null=null,version=0,cached:string|null=null,pending:Promise<string>|null=null;
 function invalidate(){version++;cached=null;pending=null}
 return {
  select(value:T|null){invalidate();selection=value},
  clear(){invalidate();selection=null},
  take(){const value=cached;invalidate();return value},
  prepare(load:(selection:T)=>Promise<string>):Promise<string>{
   if(selection===null)return Promise.reject(new Error('Select a video first.'));
   if(cached!==null)return Promise.resolve(cached);
   if(pending)return pending;
   const capturedVersion=version,capturedSelection=selection;
   const request=Promise.resolve().then(()=>{if(capturedVersion!==version)throw new StaleSelectionError();return load(capturedSelection)}).then(id=>{
    if(capturedVersion!==version)throw new StaleSelectionError();
    cached=id;return id;
   }).finally(()=>{if(capturedVersion===version)pending=null});
   pending=request;return request;
  }
 }
}
