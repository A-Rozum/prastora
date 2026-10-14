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
    const wanted=['h1','.lead','.site-header','main','footer','[data-enquiry-form]','.field-row','[name=name]','[name=email]','.member-photo'];
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
 const rows=[];
 for(const name of Object.keys(manifest.pages))for(const viewport of regimes)for(const scheme of ['light','dark']) {
  for(const fragment of ['',name==='home'?'#request':'#contact','#css-lab-footer']) {
   const baseContext=await browser.newContext({viewport,colorScheme:scheme});const base=await baseContext.newPage();
   await base.goto(origin+manifest.prefix+'/head-'+name+'.html'+fragment);await ready(base,'head');
   const expected=await sample(base);await baseContext.close();
   for(const variant of ['tail-head','tail-body']) {
    const context=await browser.newContext({viewport,colorScheme:scheme});const page=await context.newPage();
    let resume;const held=new Promise(r=>resume=r);
    await page.route('**/footer-'+name+'.css',async route=>{await held;await route.continue();});
    await page.goto(origin+manifest.prefix+'/'+variant+'-'+name+'.html'+fragment,{waitUntil:'commit'});
    await page.waitForFunction(()=>[...document.querySelectorAll('link[data-critical-css]')].every(link=>link.sheet));
    let painted=true;
    try {await page.waitForFunction(()=>performance.getEntriesByName('first-contentful-paint').length>0,{},{timeout:800});}catch{painted=false;}
    const initial=await sample(page);resume();await ready(page,variant);const final=await sample(page);
    rows.push({name,variant,viewport,scheme,fragment,painted_while_tail_held:painted,
     first_paint_differences:painted?differs(expected,initial,true):[],
     final_differences:differs(expected,final)});
    await context.close();
   }
  }
 }
 for(const variant of manifest.variants)for(const name of Object.keys(manifest.pages)) {
  const context=await browser.newContext({javaScriptEnabled:false,viewport:profiles[0].viewport});const page=await context.newPage();
  await page.goto(origin+manifest.prefix+'/'+variant+'-'+name+'.html');
  rows.push({name,variant,no_js:true,styles:await page.evaluate(()=>[...document.styleSheets].filter(s=>s.href).length)});await context.close();
 }
 return rows;
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
      tail_start_ms:resources.find(r=>/footer-(home|member)\.css$/.test(r.name))?.startTime ?? null,
      tail_end_ms:resources.find(r=>/footer-(home|member)\.css$/.test(r.name))?.responseEnd ?? null,
      tail_blocking:resources.find(r=>/footer-(home|member)\.css$/.test(r.name))?.renderBlockingStatus ?? null,
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
 const qa=await quality(remoteOrigin);await writeFile(root+'/quality.json',JSON.stringify(qa,null,2));
 console.log(JSON.stringify({phase:'placement-quality',cases:qa.length,painted_while_held:qa.filter(q=>q.painted_while_tail_held).length,
  final_mismatches:qa.filter(q=>q.final_differences?.length).length}));
 const rows=await benchmark(remoteOrigin);
 await writeFile(root+'/comparison.json',JSON.stringify({format:1,experiment:'placement',browser:browser.version(),
  source_manifest:manifest,measured_at:new Date().toISOString(),profiles,
  note:'Footer rules are split from the same minified live CSS; identical normal stylesheet links in head versus before closing body, no media or loader. Static public snapshots, HTTP/2, no-cache conditional revalidation, isolated submission disabled. Three interleaved repeats. Held-footer quality checks distinguish actual first paint from computed geometry before paint.',quality:qa,runs:rows},null,2));
} finally {await browser.close();}
