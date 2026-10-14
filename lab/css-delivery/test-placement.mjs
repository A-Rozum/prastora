import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const code=await readFile(new URL('./placement-generate.mjs',import.meta.url),'utf8');
const declaration=code.split('\n').find(line=>line.includes('const isFooter='));
const isFooter=new Function(declaration+';return isFooter;')();
for(const selector of ['.site-footer > p','.footer-links a','.inst-footer-name','.member-footer','footer p'])assert.equal(isFooter(selector),true,selector);
for(const selector of [':where(.btn,.footer-links a)','.inst-head','.member h1','.site-header','.footer-links-extra a'])assert.equal(isFooter(selector),false,selector);
console.log('PASS explicit footer selectors and mixed interactive selectors');
