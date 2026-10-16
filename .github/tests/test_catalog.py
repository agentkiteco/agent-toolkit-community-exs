import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from catalog import read_entry, collect

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.path=self.root/'skills/example/SKILL.md'
        self.path.parent.mkdir(parents=True)
    def write(self,body='Example.',name='example',description='A test example.'):
        self.path.write_text(f'---\nname: {name}\ndescription: {description}\n---\n{body}')
    def test_multiline_description(self):
        self.write(description='>\n  First line\n  second line')
        self.assertEqual(read_entry(self.path,'skill',self.root)['description'],'First line second line')
    def test_reject_missing_resource(self):
        self.write('[Read](references/missing.md)')
        with self.assertRaises(ValueError): read_entry(self.path,'skill',self.root)
    def test_reject_external_folder_dependency(self):
        (self.root/'shared.md').write_text('Shared')
        self.write('[Read](../../shared.md)')
        with self.assertRaises(ValueError): read_entry(self.path,'skill',self.root)
    def test_reject_name_mismatch(self):
        self.write(name='other')
        with self.assertRaises(ValueError): read_entry(self.path,'skill',self.root)
    def test_real_catalog(self):
        self.assertEqual({e['kind'] for e in collect()},{'skill','prompt','instruction'})
if __name__=='__main__': unittest.main()
