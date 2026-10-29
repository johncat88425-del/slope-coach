export const autoTourKeys=['real_own_2','generated_meta_clip4','generated_meta_clip2'] as const;
export function tourIndex(elapsedMs:number){return Math.min(2,Math.max(0,Math.floor(elapsedMs/10000)))}
