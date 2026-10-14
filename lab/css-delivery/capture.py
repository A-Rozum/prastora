#!/usr/bin/env python3
"""Capture public read-only fixtures; page content is identical across delivery variants."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import urllib.parse
import urllib.request

VARIANTS = ['blocking', 'async-modules', 'async-state', 'critical-inline', 'bundle', 'shared-bundle']


class Assets(HTMLParser):
    def __init__(self):
        super().__init__(); self.styles=[]; self.assets=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='link' and a.get('rel')=='stylesheet':self.styles.append(a['href']);self.assets.add(a['href'])
        if tag in ('script','img','source','use'):
            self.assets.add(a.get('src',a.get('href','')))
        if a.get('srcset'):
            self.assets.update(x.strip().split()[0] for x in a['srcset'].split(',') if x.strip())


def get(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Prastora CSS delivery comparison','Cache-Control':'no-cache'})
    with urllib.request.urlopen(request,timeout=30) as r:return r.read()


def css_link(url, deferred=False, name=''):
    if not deferred:return '<link rel="stylesheet" href="'+url+'">'
    return ('<link rel="stylesheet" href="'+url+'" media="print" data-css-defer="'+name+'" fetchpriority="low">'
            '<noscript><link rel="stylesheet" href="'+url+'"></noscript>')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--origin',required=True);p.add_argument('--output',required=True);p.add_argument('--prefix',required=True)
    args=p.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    prefix=args.prefix.rstrip('/')
    if not re.fullmatch(r'/__css-lab/[a-z0-9-]+',prefix):raise ValueError('A declared isolated fixture prefix is required.')
    pages={};assets=set();manifest={'format':1,'origin':args.origin,'prefix':prefix,'pages':{},'variants':VARIANTS}
    for name,path in [('home','/'),('member','/en/members/kryvoi')]:
        html=get(args.origin+path).decode();parser=Assets();parser.feed(html)
        pages[name]=(html,parser.styles);assets.update(parser.assets)
        manifest['pages'][name]={'source':args.origin+path,'styles':parser.styles,'source_sha256':hashlib.sha256(html.encode()).hexdigest()}
    assets={urllib.parse.urlsplit(a).path for a in assets if a.startswith('/')}
    for path in sorted(assets):
        dest=out/path.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(get(args.origin+urllib.parse.quote(path,safe='/')))
    shutil.copyfile(Path(__file__).with_name('styles.js'),out/'assets/styles.js')
    # Favicon isolates the CSS experiment from the site's implicit favicon 404.
    (out/'assets/favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M6 42V6h36v30H14V14h20v14H34v14H22v-6h6" fill="none" stroke="currentColor" stroke-width="3"/></svg>')
    shared=[s for s in pages['home'][1] if s in pages['member'][1]]
    (out/'css/shared.css').write_text('\n'.join((out/s.lstrip('/')).read_text() for s in shared))
    for name,(source,styles) in pages.items():
        # Strip session-bound form tokens and make the fixtures unable to send enquiries.
        source=re.sub(r'(<input[^>]*name="token"[^>]*value=")[^"]*',r'\1',source)
        source=source.replace('action="'+args.origin+'/', 'action="'+prefix+'/').replace('action="/','action="'+prefix+'/')
        source=re.sub(r'<link[^>]*rel="stylesheet"[^>]*>','@@STYLES@@',source,count=1)
        source=re.sub(r'<link[^>]*rel="stylesheet"[^>]*>','',source)
        # Rebase only known resource paths; navigation remains ordinary fixture material.
        for path in sorted(assets,key=len,reverse=True):source=source.replace(path,prefix+path)
        source=source.replace('</head>','<link rel="icon" href="'+prefix+'/assets/favicon.svg"></head>')
        files=[out/path.lstrip('/') for path in styles]
        # Current inputs contain no external URL/import dependencies. Refuse hidden relocation errors.
        for f in files:
            if re.search(r'@import\b|url\((?![\s\"\']*(?:data:|https?:|/))',f.read_text(),re.I):
                raise ValueError('A relative CSS resource needs rebasing before this experiment: '+str(f))
        bundle='\n'.join(f.read_text() for f in files)
        (out/'css'/('combined-'+name+'.css')).write_text(bundle)
        (out/'css'/('page-'+name+'.css')).write_text('\n'.join((out/s.lstrip('/')).read_text() for s in styles if s not in shared))
        for variant in VARIANTS:
            snippets=[]
            for path in styles:
                late=(variant=='async-modules' and path.endswith(('/forms.css','/enquiries.css'))
                      or variant=='async-state' and path.endswith('/enquiries.css')
                      or variant=='critical-inline')
                snippets.append(css_link(prefix+path,late,path.rsplit('/',1)[-1].split('.')[0]))
            if variant=='bundle':snippets=[css_link(prefix+'/css/combined-'+name+'.css')]
            if variant=='shared-bundle':snippets=[css_link(prefix+'/css/shared.css'),css_link(prefix+'/css/page-'+name+'.css')]
            if variant=='critical-inline':snippets.insert(0,'@@CRITICAL@@')
            if variant.startswith('async') or variant=='critical-inline':snippets.append('<script src="'+prefix+'/assets/styles.js" defer></script>')
            html=source.replace('@@STYLES@@','\n'.join(snippets))
            (out/(variant+'-'+name+'.html')).write_text(html)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'captured_pages':len(pages),'assets':len(assets),'variants':VARIANTS}))


if __name__=='__main__':main()
