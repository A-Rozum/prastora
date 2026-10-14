/* Optional release-only parser/minifier. No browser or PHP runtime dependency. */
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const moduleRoot=resolve(process.argv[2] || '');
const metadata=JSON.parse(readFileSync(resolve(moduleRoot,'package.json'),'utf8'));
if(metadata.name!=='lightningcss'||metadata.version!=='1.33.0')throw Error('Expected pinned lightningcss 1.33.0.');
const {transform}=createRequire(import.meta.url)(moduleRoot);
const result=transform({filename:'release.css',code:readFileSync(0),minify:true,errorRecovery:false});
if(result.warnings?.length)throw Error('Resolve CSS parser warnings before releasing: '+JSON.stringify(result.warnings));
process.stdout.write(result.code);
