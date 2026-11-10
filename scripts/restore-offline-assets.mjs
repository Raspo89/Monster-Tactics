// The download stores assets once in PLAY-OFFLINE.html, not twice in SOURCE.
import fs from 'node:fs';
import path from 'node:path';
const file=path.resolve(process.argv[2]||'../PLAY-OFFLINE.html');
const html=fs.readFileSync(file,'utf8');
let count=0;
for(const [name,directory,extension] of [['ASSETS','public/assets','.webp'],['ORIGINAL','public/assets/original',''],['MODELS','public/original3d','']]){
 const prefix=`window.__${name}__=`,start=html.indexOf(prefix);
 if(start<0)throw Error(`Missing ${name} registry`);
 const end=html.indexOf('};',start)+1;
 const registry=JSON.parse(html.slice(start+prefix.length,end));
 for(const [key,value] of Object.entries(registry)){
  const target=path.resolve(directory,key+extension),root=path.resolve(directory)+path.sep;
  if(!target.startsWith(root))throw Error('Invalid asset path');
  const match=value.match(/^data:[^;]+;base64,(.*)$/s);
  if(!match)throw Error(`Invalid asset ${key}`);
  fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,Buffer.from(match[1],'base64'));count++;
 }
}
console.log(`Restored ${count} runtime assets.`);
