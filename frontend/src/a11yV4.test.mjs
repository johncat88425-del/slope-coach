import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import ts from 'typescript';
function luminance(hex){const [r,g,b]=hex.slice(1).match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*r+.7152*g+.0722*b}
function contrast(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
test('v4 text and semantic colours retain AA contrast on every dark surface',()=>{
 for(const bg of ['#0e0f12','#17181c','#1c1e23','#101115'])for(const fg of ['#ededef','#8a8f98','#5ab0f0','#f5a524','#b7bcc5'])assert.ok(contrast(fg,bg)>=4.5,`${fg} / ${bg}`);
 for(const bg of ['#f5a524','#5ab0f0','#b7bcc5'])assert.ok(contrast('#0e0f12',bg)>=4.5);
});
test('focus discloses cards, reduced motion shows final content, and dimming never fades text',async()=>{
 const css=await readFile(new URL('./editorial.css',import.meta.url),'utf8');
 assert.match(css,/\.result-preview:has\(:focus-visible\) \.preview-evidence/);
 assert.match(css,/\.process-steps>li:focus-visible \.step-description/);
 assert.match(css,/\*,\*::before,\*::after\{animation:none!important;transition:none!important/);
 assert.match(css,/\.preview-evidence,\.step-description\{max-height:none!important;opacity:1!important\}/);
 assert.doesNotMatch(css,/result-preview:not\([^}]+opacity:\./);
});
test('all image elements have an explicit alternative and the skip link does not change the app route',async()=>{
 for(const name of (await readdir(new URL('.',import.meta.url))).filter(n=>n.endsWith('.tsx'))){
  const text=await readFile(new URL(name,import.meta.url),'utf8'),source=ts.createSourceFile(name,text,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
  function walk(node){if((ts.isJsxSelfClosingElement(node)||ts.isJsxOpeningElement(node))&&node.tagName.getText(source)==='img')assert.ok(node.attributes.properties.some(p=>ts.isJsxAttribute(p)&&p.name.text==='alt'),name);ts.forEachChild(node,walk)}walk(source);
 }
 const header=await readFile(new URL('./SiteHeader.tsx',import.meta.url),'utf8');assert.match(header,/event.preventDefault\(\)/);assert.match(header,/getElementById\('workspace'\)\?\.focus\(\)/);
});
