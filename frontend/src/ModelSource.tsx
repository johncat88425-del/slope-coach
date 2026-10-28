export function sourceLabel(source:string,kind:'understanding'|'tracking'='understanding'){
 if(source==='model')return '由 Muse Spark 產生';
 if(source==='sam')return '由 SAM 3.1 產生';
 if(source==='mock')return 'Mock 佔位資料（未呼叫模型）';
 if(source==='manual'||source==='user')return '使用者確認／人工標記';
 if(source==='frame_diff')return '影格差分追蹤（程式）';
 if(source==='physics')return '確定性 physics 計算';
 return kind==='tracking'?'追蹤來源未提供':'來源未提供';
}
export function ModelSource({source,kind}:{source:string;kind?:'understanding'|'tracking'}){return <span className="source-label">{sourceLabel(source,kind)}</span>}
