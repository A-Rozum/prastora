"""Check matter boundaries and input preconditions using invented cases. Run: python tools/pn_check_inputs.py."""
import pathlib, sys
import subprocess
import importlib.util, json, tempfile, unittest, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('ctx_select', ROOT / 'tools/pn_select.py')
sel = importlib.util.module_from_spec(spec); spec.loader.exec_module(sel)

class Inputs(unittest.TestCase):
    def setUp(self):
        (ROOT / '.context').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '.context')
        self.repo = pathlib.Path(self.tmp.name)
        self.write('system.yaml', {'id':'repo:fixture', 'kind':'project', 'access':'internal',
                                 'audience':'agent', 'description':'invented cases'})
        self.write('matters.yaml', [{'id':'a'}, {'id':'a.child'}, {'id':'b'}, {'id':'c'}])
        self.elements = [self.element('method:legal/draft', 'draft.md', requires_inputs=['decision'])]
        self.write('draft.md', 'Prepare a draft from the decision.')
        self.write('a.md', 'ALPHA_FACT')
        self.write('b.md', 'BETA_PRIVATE_FACT')
        self.write('c.md', 'GAMMA_PRIVATE_FACT')
        self.materials = [{'id':m,'matter':m,'kind':'decision','path':m+'.md','access':'public','load':'content'} for m in ['a','b','c']]
        self.save()

    def tearDown(self): self.tmp.cleanup()

    def element(self, ident, path, **kw):
        return dict(id=ident, path=path, status='trial', access='public', audience='agent', applies={'always':True}, **kw)

    def write(self, path, data):
        (self.repo / path).write_text(data if isinstance(data,str) else yaml.safe_dump(data,sort_keys=False))

    def save(self):
        self.write('elements.yaml', self.elements); self.write('materials.yaml', self.materials)

    def compile(self, *facets, success=True):
        p = subprocess.run([sys.executable,str(ROOT/'tools/pn_compile.py'),str(self.repo),*facets],capture_output=True,text=True)
        self.assertEqual(p.returncode == 0, success, p.stdout+p.stderr)
        return (self.repo/'.context/task.md').read_text() if success else p.stderr

    def validate(self, success=True):
        p = subprocess.run([sys.executable,str(ROOT/'tools/pn_validate.py'),str(self.repo)],capture_output=True,text=True)
        self.assertEqual(p.returncode == 0, success, p.stdout+p.stderr)

    def test_isolation_all_sections_before_read(self):
        for mode in ['content','head','demand','reference']:
            self.elements.append(self.element('reference:legal/foreign-'+mode,'b.md',matter='b',load=mode))
        self.save(); self.validate()
        # Guard the reader as well as the output: no foreign file may even be excerpted.
        original = sel.excerpt
        def guarded(path, mode):
            self.assertNotEqual(path.name,'b.md'); return original(path,mode)
        sel.excerpt = guarded
        try: sel.select(self.repo, {'matter':'a'}, 0)
        finally: sel.excerpt = original
        for budget in ['budget=0','budget=10000']:
            text = self.compile('matter=a',budget)
            self.assertNotIn('BETA_PRIVATE_FACT',text); self.assertNotIn('b.md',text); self.assertNotIn('foreign-',text)
        self.assertIn('ALPHA_FACT',self.compile('matter=a'))

    def test_without_matter(self):
        text=self.compile()
        self.assertNotIn('ALPHA_FACT',text); self.assertNotIn('BETA_PRIVATE_FACT',text)
        self.assertIn('missing decision',text)

    def test_links_are_directed_and_nontransitive(self):
        self.write('matters.yaml',[{'id':'a','related':['b']},{'id':'b','related':['c']},{'id':'c'}])
        self.validate()
        text=self.compile('matter=a')
        self.assertIn('BETA_PRIVATE_FACT',text); self.assertNotIn('GAMMA_PRIVATE_FACT',text)
        self.assertNotIn('ALPHA_FACT',self.compile('matter=b'))

    def test_missing_foreign_and_budget(self):
        self.elements[0]['applies']={'domain':'legal'}
        self.materials=[m for m in self.materials if m['matter']!='a']; self.save()
        text=self.compile('domain=legal','matter=a','budget=0')
        self.assertIn('Missing inputs',text); self.assertIn('method:legal/draft: missing decision',text)
        self.assertIn('Dropped by budget',text)
        self.assertNotIn('BETA_PRIVATE_FACT',text)

    def test_absent_file_and_recovery(self):
        (self.repo/'a.md').unlink();self.validate(success=False)
        self.assertIn('missing decision',self.compile('matter=a'))
        self.write('a.md','ALPHA_FACT');self.validate()
        self.assertNotIn('Missing inputs',self.compile('matter=a'))

    def test_exact_matter_identity(self):
        self.elements.append(self.element('norm:legal/exact','a.md',matter='a',applies_when='exact'))
        self.save()
        self.assertNotIn('ALPHA_FACT',self.compile('matter=a.child'))
        self.assertFalse(sel.evaluate({'matter':'a'},{'matter':'a.child'})[0])

    def test_unknown_and_multiple_matter_clear_stale_bundle(self):
        for value in ['unknown','a,b']:
            self.compile('matter=a')
            self.compile('matter='+value,success=False)
            self.assertFalse((self.repo/'.context/task.md').exists())

    def test_bad_links_and_duplicate_ids(self):
        for matters in [[{'id':'a','related':['unknown']}],[{'id':'a'},{'id':'a'}]]:
            self.write('matters.yaml',matters);self.validate(success=False);self.compile('matter=a',success=False)

    def test_bad_material_metadata(self):
        original=[dict(m) for m in self.materials]
        for field,value in [('matter','unknown'),('kind',''),('load','reference'),('path','../outside.md')]:
            self.materials=[dict(m) for m in original];self.materials[0][field]=value;self.save()
            self.validate(success=False);self.compile('matter=a',success=False)

    def test_cross_scope_alias(self):
        self.materials[1]['path']='a.md';self.save();self.validate(success=False)
        self.compile('matter=a',success=False)

    def test_global_alias_of_matter_material(self):
        self.elements.append(self.element('reference:legal/unscoped','a.md'));self.save()
        self.validate(success=False);self.compile('matter=a',success=False)

    def test_client_element_needs_matter(self):
        self.elements[0]['access']='client';self.save();self.validate(success=False)
        self.compile('matter=a',success=False)

    def test_unsafe_symlink(self):
        (self.repo/'alias.md').symlink_to(self.repo/'a.md')
        self.materials[1]['path']='alias.md';self.save()
        self.validate(success=False);self.compile('matter=a',success=False)

    def test_unregistered_file_does_not_satisfy_input(self):
        self.materials=[m for m in self.materials if m['matter']!='a'];self.save()
        self.assertIn('missing decision',self.compile('matter=a'))

    def test_material_access_inheritance(self):
        self.materials[0]['access']='client';self.save()
        self.validate(success=False);self.compile('matter=a',success=False)

    def test_invalid_input_declaration(self):
        for value in [[],['decision','decision'],'decision']:
            self.elements[0]['requires_inputs']=value;self.save()
            self.validate(success=False);self.compile('matter=a',success=False)

    def test_scoped_state_tasks(self):
        base={'status':'open','assigner':'user','executor':'executor','done_when':'accepted'}
        self.write('state.yaml',{'direction':{'text':'work'},'tasks':[dict(base,id='foreign',title='BETA_PRIVATE_FACT',matter='b'),dict(base,id='own',title='ALPHA_TASK',matter='a')]})
        self.validate();text=self.compile('matter=a')
        self.assertIn('ALPHA_TASK',text);self.assertNotIn('BETA_PRIVATE_FACT',text)

if __name__ == '__main__': unittest.main()
