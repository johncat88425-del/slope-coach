import {useEffect,useState} from 'react';
import type {createApi} from './api.js';
import {DEMO_ONLY} from './mode.js';
import {Localize} from './i18n.js';
export type Spend={total_usd:number;limit_usd:number};
/** Defensive boundary: never infer a missing amount or currency. */
export function parseSpend(value:unknown):Spend|null{if(!value||typeof value!=='object')return null;const v=value as Partial<Spend>;return typeof v.total_usd==='number'&&Number.isFinite(v.total_usd)&&v.total_usd>=0&&typeof v.limit_usd==='number'&&Number.isFinite(v.limit_usd)&&v.limit_usd>0?{total_usd:v.total_usd,limit_usd:v.limit_usd}:null}
export function SpendValue({spend}:{spend:Spend}){const money=(v:number)=>new Intl.NumberFormat('en-US',{minimumFractionDigits:2,maximumFractionDigits:6}).format(v);return <Localize><small data-testid="meta-spend" title={`USD ${spend.total_usd} / ${spend.limit_usd}`}>Meta API spend: ${money(spend.total_usd)} / ${money(spend.limit_usd)} USD</small></Localize>}
export function SpendPanel({api}:{api:ReturnType<typeof createApi>}){const [spend,setSpend]=useState<Spend|null>(null);useEffect(()=>{if(DEMO_ONLY)return;let active=true;async function refresh(){try{const value=parseSpend(await api.spend());if(active)setSpend(value)}catch{if(active)setSpend(null)}}void refresh();window.addEventListener('focus',refresh);window.addEventListener('audit-completed',refresh);return()=>{active=false;window.removeEventListener('focus',refresh);window.removeEventListener('audit-completed',refresh)}},[api]);return spend?<SpendValue spend={spend}/>:null}
