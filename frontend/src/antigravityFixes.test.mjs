import test from 'node:test';import assert from 'node:assert/strict';import {mkdtemp,rm} from 'node:fs/promises';import {tmpdir} from 'node:os';import {join} from 'node:path';import {fileURLToPath} from 'node:url';import {createServer} from 'vite';
test('T196 favicon requests return valid assets at both root and Pages base paths',async()=>{
 for(const base of ['/','/slope-coach/']){
  const cache=await mkdtemp(join(tmpdir(),'vpa-icon-test-'));
  const server=await createServer({configFile:false,root:fileURLToPath(new URL('../',import.meta.url)),base,cacheDir:cache,logLevel:'silent',optimizeDeps:{noDiscovery:true,include:[]},server:{host:'127.0.0.1',port:0}});
  try{
   await server.listen();const origin='http://127.0.0.1:'+server.httpServer.address().port;
   const page=await fetch(origin+base);assert.equal(page.status,200);const html=await page.text();assert.ok(html.includes('href="'+base+'favicon.svg"'),base+': '+JSON.stringify(html.match(/<link[^>]+>/g)));assert.ok(html.includes('href="'+base+'favicon.ico"'));
   for(const asset of ['favicon.svg','favicon.ico','favicon.png','og.png']){const response=await fetch(origin+base+asset);assert.equal(response.status,200,base+asset);assert.ok((await response.arrayBuffer()).byteLength>0)}
  }finally{await server.close();await rm(cache,{recursive:true,force:true})}
 }
});
