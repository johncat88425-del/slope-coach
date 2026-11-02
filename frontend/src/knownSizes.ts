// T254: official diameters of common balls, offered as a one-click suggestion the user must confirm.
// A fixed table, never a model estimate; toy or mini balls differ, so the button says which standard it uses.
export type KnownSize={label:string;metres:number};
const TABLE:[RegExp,KnownSize][]=[
 [/basket ?ball/i,{label:'a regulation basketball (size 7)',metres:0.24}],
 [/soccer|football(?! american)/i,{label:'a regulation football (size 5)',metres:0.22}],
 [/volley ?ball/i,{label:'a regulation volleyball',metres:0.21}],
 [/tennis/i,{label:'a regulation tennis ball',metres:0.067}],
 [/ping ?pong|table tennis/i,{label:'a regulation table-tennis ball',metres:0.04}],
 [/golf/i,{label:'a regulation golf ball',metres:0.043}],
 [/baseball/i,{label:'a regulation baseball',metres:0.074}],
 [/softball/i,{label:'a regulation softball',metres:0.097}],
 [/cricket/i,{label:'a regulation cricket ball',metres:0.072}],
];
export function knownSize(objectName:string):KnownSize|null{
 for(const [pattern,size] of TABLE)if(pattern.test(objectName))return size;
 return null;
}
