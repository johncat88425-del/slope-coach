import {defineConfig} from 'vite';
import {readFileSync} from 'node:fs';

// UI test only: serve the existing synthetic clip with seeking, and block all real API traffic.
const clip=readFileSync(new URL('../../data/samples/synthetic_toss_earth_g.mp4',import.meta.url));
export default defineConfig({server:{host:'127.0.0.1',port:5192,strictPort:true},plugins:[{name:'point-selection-fixture',configureServer(server){
 server.middlewares.use((req,res,next)=>{
  if(req.url==='/media/t270-fixture.mp4'){
   const range=/^bytes=(\d+)-(\d*)$/.exec(req.headers.range??''),first=range?Number(range[1]):0,last=range&&range[2]?Math.min(clip.length-1,Number(range[2])):clip.length-1;
   if(first>last||first>=clip.length){res.statusCode=416;res.end();return}
   res.setHeader('Content-Type','video/mp4');res.setHeader('Accept-Ranges','bytes');res.setHeader('Content-Length',last-first+1);
   if(range){res.statusCode=206;res.setHeader('Content-Range',`bytes ${first}-${last}/${clip.length}`)}
   res.end(req.method==='HEAD'?undefined:clip.subarray(first,last+1));return;
  }
  if(/^\/(api|media)(\/|$)/.test(req.url??'')){res.statusCode=503;res.end('No backend is connected to this UI test.');return}
  next();
 });
}}]});
