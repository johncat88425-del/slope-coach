/** Presentation only: returns text; never mutates backend values. */
export function formatNumber(value:number,key=''){
 if(!Number.isFinite(value))return '—';
 if(key==='g_vs_earth'&&value>=0&&value<.01)return 'less than 1/100 of Earth';
 if(value===0)return '0';
 if(/size|length/.test(key))return value.toPrecision(3);
 if(Math.abs(value)<0.001||Math.abs(value)>=1e7)return value.toExponential(2);
 const digits=/ratio|g_vs_earth|factor|fraction|spread/.test(key)?2:3;
 const rounded=Number(value.toFixed(digits));return rounded===0?value.toExponential(2):String(rounded);
}
