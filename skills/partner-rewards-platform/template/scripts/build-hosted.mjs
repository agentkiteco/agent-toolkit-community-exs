import {readFileSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {build} from '../cloud/node_modules/esbuild/lib/main.js';
const assets={};
for(const [url,path,type] of [['/','static/index.html','text/html; charset=utf-8'],['/static/app.js','static/app.js','text/javascript; charset=utf-8'],['/static/styles.css','static/styles.css','text/css; charset=utf-8']]) assets[url]={body:readFileSync(path,'utf8'),type};
writeFileSync('hosted/assets.js','export const assets='+JSON.stringify(assets)+';\n');
mkdirSync('dist/server',{recursive:true});mkdirSync('dist/.openai',{recursive:true});
await build({entryPoints:['hosted/worker.js'],bundle:true,format:'esm',platform:'browser',target:'es2022',outfile:'dist/server/index.js'});
copyFileSync('.openai/hosting.json','dist/.openai/hosting.json');
