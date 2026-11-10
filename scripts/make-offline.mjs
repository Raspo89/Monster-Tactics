import fs from 'node:fs';
import path from 'node:path';
const out=path.resolve(process.argv[2]||'release');fs.mkdirSync(out,{recursive:true});
const mime={'.webp':'image/webp','.png':'image/png','.wav':'audio/wav','.json':'application/json'};
function registry(root,filter=()=>true){const result={};function walk(dir){for(const d of fs.readdirSync(dir,{withFileTypes:true})){const f=path.join(dir,d.name);if(d.isDirectory())walk(f);else if(mime[path.extname(f)]&&filter(f))result[path.relative(root,f).replaceAll('\\','/')] = 'data:'+mime[path.extname(f)]+';base64,'+fs.readFileSync(f).toString('base64');}}walk(root);return result;}
const raw=registry('public/assets',f=>path.dirname(f)==='public/assets');const assets=Object.fromEntries(Object.entries(raw).map(([k,v])=>[k.slice(0,-5),v]));
const original=registry('public/assets/original');const models=registry('public/original3d',f=>!f.includes('/world/')&&!f.includes('/props/'));
const index=fs.readFileSync('dist/index.html','utf8'),jsFile=index.match(/src="([^"]+\.js)"/)[1],cssFile=index.match(/href="([^"]+\.css)"/)[1];
const js=fs.readFileSync('dist/'+jsFile.replace(/^\//,''),'utf8').replace(/<\/script/gi,'<\\/script');let css=fs.readFileSync('dist/'+cssFile.replace(/^\//,''),'utf8').replaceAll('/assets/arena.webp',assets.arena);
for(const [p,data] of Object.entries(original))css=css.replaceAll('/assets/original/'+p,data);
const html=`<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"><title>وحوش المعركة • الإصدار 7.7 • دون إنترنت</title><style>${css}</style></head><body><div id="app"></div><script>window.__ASSETS__=${JSON.stringify(assets)};window.__ORIGINAL__=${JSON.stringify(original)};window.__MODELS__=${JSON.stringify(models)};<\/script><script type="module">${js}<\/script></body></html>`;
fs.writeFileSync(path.join(out,'PLAY-OFFLINE.html'),html);console.log(JSON.stringify({file:path.join(out,'PLAY-OFFLINE.html'),bytes:Buffer.byteLength(html),legacyAssets:Object.keys(assets).length,originalAssets:Object.keys(original).length,modelFiles:Object.keys(models).length}));
