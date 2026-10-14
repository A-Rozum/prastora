import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('styles', Path(__file__).with_name('styles.py'))
styles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styles)


class Bundles(unittest.TestCase):
    def test_order_and_dependency_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'a.css').write_text('@layer core, theme, components;\n@layer components {a{color:red}}')
            (root/'b.css').write_text('@layer components {a{color:blue}}')
            plan = {'format':1, 'bundles':{'/bundle.css':['/a.css','/b.css']}}
            first = styles.generate(root, plan)['/bundle.css']
            self.assertLess(first['body'].index(b'color:red'), first['body'].index(b'color:blue'))
            (root/'a.css').write_text('@layer components {a{color:green}}')
            second = styles.generate(root, plan)['/bundle.css']
            self.assertNotEqual(first['sha256'], second['sha256'])
            self.assertNotEqual(first['sources'][0]['sha256'], second['sources'][0]['sha256'])

    def test_relocation_and_escape_fail_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for css in ['a{background:url(../image.svg)}', '@import "b.css";']:
                (root/'a.css').write_text(css)
                with self.assertRaises(ValueError):
                    styles.generate(root, {'format':1,'bundles':{'/bundle.css':['/a.css']}})
            (root/'a.css').write_text('a{background:url(/image.svg)}')
            styles.generate(root, {'format':1,'bundles':{'/bundle.css':['/a.css']}})
            with self.assertRaises(ValueError):
                styles.generate(root, {'format':1,'bundles':{'/../bundle.css':['/a.css']}})
            with self.assertRaises(ValueError):
                styles.generate(root, {'format':1,'bundles':{'/bundle.css':['/bundle.css']}})


if __name__ == '__main__':
    unittest.main()
