import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const code=await readFile(new URL('./styles.js',import.meta.url),'utf8');
function fixture(cached=false) {
  const handlers=new Map(),timers=[];
  const link={media:'print',sheet:cached?{}:null,dataset:{cssDefer:'widget',cssMedia:'screen'},
    addEventListener:(name,cb)=>handlers.set(name,cb),removeEventListener:name=>handlers.delete(name)};
  const window={};const document={querySelectorAll:()=>[link]};
  vm.runInNewContext(code,{window,document,setTimeout:cb=>{timers.push(cb);return 1},clearTimeout:()=>{}});
  return {link,window,handlers,timers};
}
let f=fixture(true);
assert.equal(await f.window.PrastoraStyles.ready('widget'),true);assert.equal(f.link.media,'screen');
f=fixture();const ready=f.window.PrastoraStyles.ready('widget');f.handlers.get('load')();
assert.equal(await ready,true);assert.equal(f.link.dataset.cssState,'ready');
f=fixture();const failed=f.window.PrastoraStyles.ready('widget');f.handlers.get('error')();
assert.equal(await failed,false);assert.equal(f.link.media,'print');
f=fixture();const timeout=f.window.PrastoraStyles.ready('widget');f.timers[0]();assert.equal(await timeout,false);
assert.equal(await f.window.PrastoraStyles.ready('absent'),true);
console.log('PASS cached/load/error/timeout/missing stylesheet readiness');
