export function elapsedSeconds(start:number,now:number){return Math.max(0,Math.floor((now-start)/1000))}
/** A discrete UI double-click must never dispatch the same mutation twice. */
export function createRequestGate(){let running=false;return async function run<T>(action:()=>Promise<T>):Promise<T|undefined>{if(running)return;running=true;try{return await action()}finally{running=false}}}
