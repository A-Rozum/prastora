import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {createServer} from 'node:http';
import {resolve,extname} from 'node:path';
import {pathToFileURL} from 'node:url';
const {chromium} = await import(pathToFileURL(process.env.CSS_BROWSER_MODULE).href);
const [operation, directory, remoteOrigin, repetitions='3'] = process.argv.slice(2);
const root=resolve(directory);
const manifest=JSON.parse(await readFile(root+'/manifest.json'));
const profiles=[
  {name:'mobile',viewport:{width:390,height:844},latency:150,rate:1600000/8,cpu:4},
  {name:'desktop',viewport:{width:1280,height:900},latency:20,rate:10000000/8,cpu:1}
];
const regimes=[{width:390,height:844},{width:1280,height:900},{width:2560,height:1440},{width:1024,height:280}];
const browser=await chromium.launch();
const hash=css=>'sha256-'+createHash('sha256').update(css).digest('base64');
const csp=hashes=>"default-src 'none'; script-src 'self'; style-src 'self' "+hashes.join(' ')+"; img-src 'self' data:; font-src 'self'; connect-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'none'";

async function sample(page) {
  return page.evaluate(()=>{
    const wanted=['h1','.lead','.site-header','main','[data-enquiry-form]','.field-row','[name=name]','[name=email]','.member-photo'];
    return Object.fromEntries(wanted.map(selector=>{
      const el=document.querySelector(selector);
      if(!el)return [selector,null];
      const r=el.getBoundingClientRect(),s=getComputedStyle(el);
      return [selector,{x:Math.round(r.x*10)/10,y:Math.round(r.y*10)/10,width:Math.round(r.width*10)/10,
        // Main's total offscreen height may change, while its visible position must remain stable.
        height:selector==='main'?null:Math.round(r.height*10)/10,font:s.fontSize,color:s.color,display:s.display,
        visible:r.bottom>0 && r.top<innerHeight && r.width>0 && r.height>0}];
    }));
  });
}

async function ready(page,variant) {
  await page.waitForLoadState('load');
  if(variant.startsWith('async')||variant==='critical-inline') {
    await page.waitForFunction(()=>window.PrastoraStyles);
    await page.evaluate(()=>window.PrastoraStyles.ready());
  }
  await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
}

async function extract(origin,name) {
  const used=new Set();let structure;
  for(const viewport of regimes)for(const scheme of ['light','dark']) {
    const context=await browser.newContext({viewport,colorScheme:scheme});const page=await context.newPage();
    await page.goto(origin+manifest.prefix+'/blocking-'+name+'.html');await ready(page,'blocking');
    const data=await page.evaluate(()=>{
      const selected=[];
      const visible=el=>{
        if(el===document.documentElement||el===document.body)return true;
        const r=el.getBoundingClientRect();return r.width>0 && r.height>0 && r.bottom>0 && r.top<innerHeight;
      };
      const walk=(rules,prefix)=>[...rules].map((rule,i)=>{
        const key=prefix+'.'+i;
        if(rule.selectorText){
          let matches=false;
          try {
            const selector=rule.selectorText.replace(/::[a-z-]+(?:\([^)]*\))?/gi,'').replace(/:(?:hover|active|focus-visible|focus|visited)\b/g,'');
            matches=[...document.querySelectorAll(selector)].some(visible);
          } catch {matches=true;}
          if(matches)selected.push(key);
          return {key,text:rule.cssText};
        }
        if(rule.cssRules && !rule.cssText.startsWith('@keyframes'))return {key,header:rule.cssText.slice(0,rule.cssText.indexOf('{')),children:walk(rule.cssRules,key)};
        selected.push(key);return {key,text:rule.cssText};
      });
      const sheets=[...document.styleSheets].filter(s=>s.href).map((s,i)=>({href:s.href,nodes:walk(s.cssRules,'s'+i)}));
      return {selected,sheets};
    });
    data.selected.forEach(k=>used.add(k));structure=data.sheets;
    await context.close();
  }
  const serial=nodes=>nodes.map(n=>{
    if(n.children){const inner=serial(n.children);return inner?n.header+'{'+inner+'}':'';}
    return used.has(n.key)?n.text:'';
  }).join('\n');
  const css=structure.map(s=>serial(s.nodes)).join('\n');
  // Inputs captured for this experiment contain no relative CSS URL dependencies.
  assert.ok(!css.includes('</style'));
  let html=await readFile(root+'/critical-inline-'+name+'.html','utf8');
  html=html.replace('@@CRITICAL@@','<style>'+css+'</style>');
  await writeFile(root+'/critical-inline-'+name+'.html',html);
  await writeFile(root+'/critical-'+name+'.css',css);
  return {bytes:Buffer.byteLength(css),hash:"'"+hash(css)+"'"};
}

async function generate() {
  const server=createServer(async(req,res)=>{
    try {
      const path=new URL(req.url,'http://local').pathname;
      const local=resolve(root,path.slice(manifest.prefix.length+1));
      if(!path.startsWith(manifest.prefix+'/')||!local.startsWith(root+'/'))throw Error('path');
      const body=await readFile(local);
      const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.webp':'image/webp'};
      res.writeHead(200,{'Content-Type':types[extname(local)]||'application/octet-stream','Content-Security-Policy':csp([]),'X-Robots-Tag':'noindex,nofollow'});res.end(body);
    } catch {res.writeHead(404);res.end();}
  });
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
  const critical={};
  try {for(const name of Object.keys(manifest.pages))critical[name]=await extract(origin,name);}finally{server.close();}
  const policy=csp(Object.values(critical).map(x=>x.hash));
  await writeFile(root+'/.htaccess','Options -Indexes\n<IfModule mod_headers.c>\nHeader always set X-Robots-Tag "noindex, nofollow"\nHeader always set Cache-Control "no-cache"\nHeader always set Content-Security-Policy "'+policy+'"\n</IfModule>\n');
  manifest.critical=critical;manifest.browser=browser.version();manifest.profiles=profiles;
  await writeFile(root+'/manifest.json',JSON.stringify(manifest,null,2));
  console.log(JSON.stringify({phase:'generated',critical,browser:browser.version()}));
}

function differs(expected,actual,visibleOnly=false) {
  const diffs=[];
  for(const [key,a] of Object.entries(expected)) {
    const b=actual[key];if(!a||!b)continue;if(visibleOnly && !a.visible)continue;
    for(const prop of ['x','y','width','height','font','color','display']) {
      if(a[prop]===null)continue;
      const delta=typeof a[prop]==='number'?Math.abs(a[prop]-b[prop])>1:a[prop]!==b[prop];
      if(delta)diffs.push(key+'.'+prop);
    }
  }
  return diffs;
}

async function quality(origin) {
  const results=[];
  for(const name of Object.keys(manifest.pages))for(const viewport of regimes)for(const scheme of ['light','dark']) {
    const anchor=name==='home'?'request':'contact';
    for(const fragment of ['', '#'+anchor]) {
      const baselineContext=await browser.newContext({viewport,colorScheme:scheme});const base=await baselineContext.newPage();
      await base.goto(origin+manifest.prefix+'/blocking-'+name+'.html'+fragment);await ready(base,'blocking');const expected=await sample(base);await baselineContext.close();
      for(const variant of manifest.variants.filter(v=>v!=='blocking')) {
        const context=await browser.newContext({viewport,colorScheme:scheme});const page=await context.newPage();
        let resume;const held=new Promise(r=>resume=r);const late=new Set(
          variant==='critical-inline'?manifest.pages[name].styles:
          variant==='async-modules'?manifest.pages[name].styles.filter(p=>p.endsWith('/forms.css')||p.endsWith('/enquiries.css')):
          variant==='async-state'?manifest.pages[name].styles.filter(p=>p.endsWith('/enquiries.css')):[]);
        if(late.size)await page.route('**/*.css',async route=>{
          const path=new URL(route.request().url()).pathname.slice(manifest.prefix.length);
          if(late.has(path))await held;await route.continue();
        });
        await page.goto(origin+manifest.prefix+'/'+variant+'-'+name+'.html'+fragment,{waitUntil:'commit'});
        await page.waitForFunction(()=>performance.getEntriesByName('first-contentful-paint').length>0);
        await page.waitForFunction(()=>document.querySelector('[data-viewport-value]')?.textContent);
        await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
        const initial=await sample(page);const early=differs(expected,initial,true);
        resume();await ready(page,variant);const final=await sample(page);const complete=differs(expected,final);
        results.push({name,variant,viewport,scheme,fragment,first_paint_differences:early,final_differences:complete});
        await context.close();
      }
    }
  }
  for(const variant of manifest.variants)for(const name of Object.keys(manifest.pages)) {
    const context=await browser.newContext({viewport:profiles[0].viewport,javaScriptEnabled:false});const page=await context.newPage();
    const errors=[];page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    await page.goto(origin+manifest.prefix+'/'+variant+'-'+name+'.html');
    const css=await page.evaluate(()=>[...document.styleSheets].filter(s=>s.href&&matchMedia(s.media.mediaText||'all').matches).length);
    results.push({name,variant,no_js:true,applied_stylesheets:css,console_errors:errors.length});await context.close();
  }
  return results;
}

const initMetrics=()=>{
  window.__cssMetrics={lcp:0,cls:0,longTasks:[]};
  for(const type of ['largest-contentful-paint','layout-shift','longtask'])new PerformanceObserver(list=>{
    for(const e of list.getEntries()){
      if(type==='largest-contentful-paint')window.__cssMetrics.lcp=e.startTime;
      if(type==='layout-shift'&&!e.hadRecentInput)window.__cssMetrics.cls+=e.value;
      if(type==='longtask')window.__cssMetrics.longTasks.push({start:e.startTime,duration:e.duration});
    }
  }).observe({type,buffered:true});
};

async function measure(page,origin,variant,name,profile) {
  const session=await page.context().newCDPSession(page);
  await session.send('Network.enable');await session.send('Network.emulateNetworkConditions',{offline:false,latency:profile.latency,downloadThroughput:profile.rate,uploadThroughput:profile.rate/2});
  await session.send('Emulation.setCPUThrottlingRate',{rate:profile.cpu});
  await page.goto(origin+manifest.prefix+'/'+variant+'-'+name+'.html');await ready(page,variant);
  await page.waitForTimeout(800);
  const metrics=await page.evaluate(()=>{
    const nav=performance.getEntriesByType('navigation')[0];const m=window.__cssMetrics;
    const fcp=performance.getEntriesByName('first-contentful-paint')[0]?.startTime||0;
    const resources=performance.getEntriesByType('resource');
    return {fcp_ms:fcp,lcp_ms:m.lcp,cls:m.cls,ttfb_ms:nav.responseStart,load_ms:nav.loadEventEnd,
      blocking_ms:m.longTasks.filter(t=>t.start>=fcp).reduce((n,t)=>n+Math.max(0,t.duration-50),0),
      transferred_bytes:nav.transferSize+resources.reduce((n,r)=>n+r.transferSize,0),
      requests:1+resources.length,css_requests:resources.filter(r=>r.name.includes('.css')).length,
      protocol:nav.nextHopProtocol};
  });
  await session.detach();return metrics;
}

async function benchmark(origin) {
  const rows=[];
  // Interleave variants and rotate order per repetition rather than measure one strategy in a block.
  for(const profile of profiles)for(let run=0;run<Number(repetitions);run++) {
    const order=manifest.variants.slice(run).concat(manifest.variants.slice(0,run));
    for(const name of Object.keys(manifest.pages))for(const variant of order) {
      const context=await browser.newContext({viewport:profile.viewport});await context.addInitScript(initMetrics);const page=await context.newPage();
      for(const cache of ['cold','repeat']) {
        const metrics=await measure(page,origin,variant,name,profile);rows.push({profile:profile.name,run,name,variant,cache,...metrics});
        console.log(JSON.stringify({profile:profile.name,name,variant,cache,fcp_ms:Math.round(metrics.fcp_ms),lcp_ms:Math.round(metrics.lcp_ms),cls:metrics.cls}));
      }
      // Measure navigation to a different layout using the same cache, without inventing a cache policy.
      if(name==='home') {const metrics=await measure(page,origin,variant,'member',profile);rows.push({profile:profile.name,run,name:'member',variant,cache:'from-home',...metrics});}
      await context.close();
    }
  }
  return rows;
}

try {
  if(operation==='generate')await generate();
  else {
    const qa=await quality(remoteOrigin);await writeFile(root+'/quality.json',JSON.stringify(qa,null,2));
    console.log(JSON.stringify({phase:'quality',cases:qa.length,final_mismatches:qa.filter(x=>x.final_differences?.length).length,
      first_paint_mismatches:qa.filter(x=>x.first_paint_differences?.length).length}));
    const rows=await benchmark(remoteOrigin);
    const report={format:1,source_manifest:manifest,browser:browser.version(),measured_at:new Date().toISOString(),
      note:'Same public HTML snapshots on the real HTTPS host; native browser metrics under declared network/CPU conditions. Blocking time is excess long-task duration after FCP in this observation window, not Lighthouse TTI-based TBT.',quality:qa,runs:rows};
    await writeFile(root+'/comparison.json',JSON.stringify(report,null,2));
  }
} finally {await browser.close();}
