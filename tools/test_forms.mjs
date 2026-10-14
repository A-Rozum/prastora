import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const {chromium}=await import(pathToFileURL(process.env.CSS_BROWSER_MODULE).href);
const {transform}=createRequire(import.meta.url)(resolve(process.env.PRASTORA_LIGHTNING_CSS));
const core=readFileSync('css/core.css','utf8'),forms=readFileSync('css/components/forms.css','utf8');
const browser=await chromium.launch();
let cases=0;
try {
 for(const theme of ['default','expertise-institution'])for(const scheme of ['light','dark'])for(const width of [390,1280,2560]) {
  const css=core+'\n'+readFileSync('css/themes/'+theme+'.css','utf8')+'\n'+forms;
  let expected;
  for(const minify of [false,true]) {
   const context=await browser.newContext({viewport:{width,height:844},colorScheme:scheme});
   const page=await context.newPage();
   const source=minify?transform({filename:'forms.css',code:Buffer.from(css),minify:true}).code.toString():css;
   await page.setContent('<style>'+source+'</style><form><label class="field"><span>Email</span><input id="email" type="email" required aria-describedby="error"><span id="error" class="field-error">Enter a valid email.</span></label><p class="form-status" data-state="idle" role="status"></p><button type="submit">Send</button></form>');
   const input=page.locator('input'),error=page.locator('.field-error'),status=page.locator('.form-status');
   assert.equal(await error.isVisible(),false,'untouched required input has no error');
   assert.equal(await status.isVisible(),false,'empty status takes no space');
   await page.locator('button').click();
   assert.equal(await input.evaluate(el=>el.matches(':user-invalid')),true);
   assert.equal(await error.isVisible(),true,'native error is shown');
   await input.fill('valid@example.invalid');await input.press('Tab');
   await input.evaluate(el=>el.setAttribute('aria-invalid','true'));
   assert.equal(await error.isVisible(),true,'server state does not require native invalidity');
   assert.equal(await input.evaluate(el=>el.validity.valid),true);
   await error.evaluate(el=>el.textContent='');
   assert.equal(await error.isVisible(),false,'empty error slots remain hidden');
   await status.evaluate(el=>{el.dataset.state='error';el.setAttribute('role','alert');el.textContent='Submission failed.';});
   const state=await page.evaluate(()=>{
    const i=document.querySelector('input'),s=document.querySelector('.form-status');
    const r=i.getBoundingClientRect();return {border:getComputedStyle(i).borderTopColor,color:getComputedStyle(s).color,
     statusBorder:getComputedStyle(s).borderLeftStyle,x:r.x,y:r.y,width:r.width,height:r.height};
   });
   assert.equal(state.border,state.color);assert.equal(state.statusBorder,'solid');
   await page.locator('button').evaluate(el=>el.hidden=true);
   assert.equal(await page.locator('button').isVisible(),false,'hidden submit remains hidden');
   if(expected)assert.deepEqual(state,expected,'minification preserves geometry and state colours');else expected=state;
   await context.close();cases++;
  }
 }
 console.log('PASS '+cases+' native/server/empty/error/hidden/minification form cases');
} finally {await browser.close();}
