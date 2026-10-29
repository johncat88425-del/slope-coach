export {openingExampleKeys as autoTourKeys} from './demoSelection.js';
export function tourIndex(elapsedMs:number){return Math.min(2,Math.max(0,Math.floor(elapsedMs/10000)))}
