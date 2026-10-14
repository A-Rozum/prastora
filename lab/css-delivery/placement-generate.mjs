import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {createServer} from 'node:http';
const {chromium}=await import(pathToFileURL(process.env.CSS_BROWSER_MODULE).href);
const {transform}=createRequire(import.meta.url)(resolve(process.env.PRASTORA_LIGHTNING_CSS));
const root=resolve(process.argv[2]);
const manifest=JSON.parse(await readFile(root+'/manifest.json'));
const prefix=manifest.prefix;
const browser=await chromium.launch();
const server=createServer(async(req,res)=>{
 try {const path=new URL(req.url,'http://local').pathname;const file=resolve(root,path.slice(prefix.length+1));
  if(!path.startsWith(prefix+'/')||!file.startsWith(root+'/'))throw Error('path');
  const body=await readFile(file);res.writeHead(200,{'Content-Type':file.endsWith('.css')?'text/css':file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':'application/octet-stream'});res.end(body);
 }catch{res.writeHead(404);res.end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin='http://127.0.0.1:'+server.address().port;
const minify=css=>transform({filename:'placement.css',code:Buffer.from(css),minify:true,errorRecovery:false}).code.toString();
try {
 for(const name of Object.keys(manifest.pages)) {
  const context=await browser.newContext();const page=await context.newPage();await page.goto(origin+prefix+'/blocking-'+name+'.html');
  const split=await page.evaluate(()=>{
   const selectors=text=>{
    let depth=0,quote='',escape=false,start=0;const out=[];
    for(let i=0;i<text.length;i++){const c=text[i];if(escape){escape=false;continue;}if(c==='\\'){escape=true;continue;}
     if(quote){if(c===quote)quote='';continue;}if(c==='"'||c==="'"){quote=c;continue;}
     if(c==='('||c==='[')depth++;else if(c===')'||c===']')depth--;else if(c===','&&depth===0){out.push(text.slice(start,i).trim());start=i+1;}
    }out.push(text.slice(start).trim());return out;
   };
   const partition=rules=>{
    let main='',late='';
    for(const rule of rules){
     if(rule.selectorText){
      const list=selectors(rule.selectorText),footer=list.filter(s=>/footer/.test(s)),other=list.filter(s=>!/footer/.test(s));
      if(other.length)main+=other.join(',')+'{'+rule.style.cssText+'}\n';
      if(footer.length)late+=footer.join(',')+'{'+rule.style.cssText+'}\n';
     }else if(rule.cssRules){const child=partition(rule.cssRules);const header=rule.cssText.slice(0,rule.cssText.indexOf('{'));
      if(child.main)main+=header+'{'+child.main+'}\n';if(child.late)late+=header+'{'+child.late+'}\n';
     }else main+=rule.cssText+'\n';
    }return {main,late};
   };
   const sheets=[...document.styleSheets].filter(s=>s.href);
   const core=sheets[0].href;
   const parts=sheets.slice(1).map(s=>partition(s.cssRules));
   return {core,main:parts.map(p=>p.main).join('\n'),late:parts.map(p=>p.late).join('\n')};
  });
  if(!split.late)throw Error('The captured page has no footer module to compare.');
  await writeFile(root+'/css/main-'+name+'.css',minify(split.main));
  await writeFile(root+'/css/footer-'+name+'.css',minify(split.late));
  let html=await readFile(root+'/blocking-'+name+'.html','utf8');
  html=html.replace(/<footer\b[^>]*>/,tag=>tag.replace(/\s+id="[^"]*"/,'').replace('>',' id="css-lab-footer">'));
  const links=[...html.matchAll(/<link[^>]*rel="stylesheet"[^>]*>/g)].map(m=>m[0]);
  const coreLink=links[0].replace('>',' data-critical-css>');
  let base=html.replace(/<link[^>]*rel="stylesheet"[^>]*>/g,'');
  const common=coreLink+'\n<link rel="stylesheet" href="'+prefix+'/css/main-'+name+'.css" data-critical-css>';
  const footer='<link rel="stylesheet" href="'+prefix+'/css/footer-'+name+'.css">';
  await writeFile(root+'/head-'+name+'.html',html.replaceAll('<link rel="stylesheet"','<link data-critical-css rel="stylesheet"'));
  await writeFile(root+'/tail-head-'+name+'.html',base.replace('</head>',common+'\n'+footer+'\n</head>'));
  await writeFile(root+'/tail-body-'+name+'.html',base.replace('</head>',common+'\n</head>').replace('</body>',footer+'\n</body>'));
  manifest.pages[name].tail={path:'/css/footer-'+name+'.css',bytes:Buffer.byteLength(minify(split.late))};
  await context.close();
 }
 manifest.variants=['head','tail-head','tail-body'];manifest.experiment='placement';manifest.browser=browser.version();
 await writeFile(root+'/manifest.json',JSON.stringify(manifest,null,2));
 await writeFile(root+'/.htaccess',`Options -Indexes\n<IfModule mod_headers.c>\nHeader always set X-Robots-Tag "noindex, nofollow"\nHeader always set Cache-Control "no-cache"\nHeader always set Content-Security-Policy "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'"\n</IfModule>\n`);
 console.log(JSON.stringify({phase:'placement-generated',variants:manifest.variants,tail:Object.fromEntries(Object.entries(manifest.pages).map(([k,p])=>[k,p.tail]))}));
} finally {server.close();await browser.close();}
