/** Presentation only: returns text; never mutates backend values. */
export function formatNumber(value:number,key=''){
 if(!Number.isFinite(value))return '—';if(value===0)return '0';
 if(Math.abs(value)<0.001||Math.abs(value)>=1e7)return value.toExponential(2);
 const digits=/size|length/.test(key)?1:/ratio|g_vs_earth|factor|fraction|spread/.test(key)?2:3;
 const rounded=Number(value.toFixed(digits));return rounded===0?value.toExponential(2):String(rounded);
}
