import sys,tempfile,json,hashlib,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from combatlens.runtime.presentation import resolve
from combatlens.runtime.server import create_server
from combatlens.runtime.repository import Config
from combatlens.orchestrator import demo

class PresentationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.research=self.root/'run';self.research.mkdir();self.repo=SimpleNamespace(root=self.root,research_dir=self.research)
  self.folder=self.root/'local/presentations/reviewed';self.folder.mkdir(parents=True)
  self.raw=bytes.fromhex('89504e470d0a1a0a')+b'synthetic-image-fixture';self.image=self.folder/'hero.png';self.image.write_bytes(self.raw)
  self.theme={'schema':'combatlens-presentation/1','title':'Synthetic subject','palette':{'accent':'#ddaa77'},'hero':{'path':'reviewed/hero.png','sha256':hashlib.sha256(self.raw).hexdigest(),'source_url':'https://example.org/source','credit':'Synthetic'}}
  self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):
  (self.folder/'theme.json').write_text(json.dumps(self.theme),encoding='utf-8');(self.research/'run-report.json').write_text(json.dumps({'adapter':'reviewed'}),encoding='utf-8')
 def test_inherited_theme_and_sanitized_asset_contract(self):
  result,path=resolve(self.repo);self.assertEqual(result['status'],'ready');self.assertEqual(path,self.image.resolve());self.assertEqual(result['hero']['url'],'/api/presentation/hero');self.assertNotIn(str(self.root),json.dumps(result))
  later=self.root/'later';later.mkdir();(later/'run-report.json').write_text('{"adapter":"reviewed"}');self.assertEqual(resolve(SimpleNamespace(root=self.root,research_dir=later))[0],result)
 def test_missing_theme_has_offline_default(self):
  (self.research/'run-report.json').unlink();self.assertEqual(resolve(self.repo)[0]['status'],'default');self.assertIsNone(resolve(self.repo)[1])
 def test_traversal_absolute_paths_and_non_image_are_rejected(self):
  for value in ('../secret.png',str(self.image.resolve()),'reviewed/secret.svg'):
   with self.subTest(value=value):
    self.theme['hero']['path']=value;self.write();r,p=resolve(self.repo);self.assertEqual(r['status'],'unavailable');self.assertIsNone(p)
 def test_changed_digest_bad_colors_and_bad_json_use_diagnostic(self):
  self.image.write_bytes(self.raw+b'changed');self.assertEqual(resolve(self.repo)[0]['status'],'unavailable');self.image.write_bytes(self.raw)
  for color in ('red','url(secret)','#fff'):
   self.theme['palette']['accent']=color;self.write();self.assertEqual(resolve(self.repo)[0]['status'],'unavailable')
  (self.folder/'theme.json').write_text('[]');self.assertEqual(resolve(self.repo)[0]['status'],'unavailable')
 def test_symlink_escape_is_rejected(self):
  external=self.root/'outside.png';external.write_bytes(self.raw);self.image.unlink()
  try:self.image.symlink_to(external)
  except OSError:self.skipTest('Symlink privilege unavailable')
  self.assertEqual(resolve(self.repo)[0]['status'],'unavailable')
 def test_run_override_and_https_attribution(self):
  override=dict(self.theme,title='Pinned');(self.research/'presentation.json').write_text(json.dumps(override),encoding='utf-8');self.assertEqual(resolve(self.repo)[0]['title'],'Pinned')
  override['hero']['source_url']='javascript:alert(1)';(self.research/'presentation.json').write_text(json.dumps(override),encoding='utf-8');self.assertEqual(resolve(self.repo)[0]['status'],'unavailable')
 def test_live_default_theme_and_unregistered_asset(self):
  result=demo(self.root);server=create_server(Config(self.root,research_dir=Path(result['research_dir'])),port=0);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
  base='http://127.0.0.1:'+str(server.server_port)
  try:
   with urlopen(base+'/api/presentation') as r:self.assertEqual(json.load(r)['status'],'default')
   with self.assertRaises(HTTPError) as raised:urlopen(base+'/api/presentation/hero')
   self.assertEqual(raised.exception.code,404)
  finally:server.shutdown();server.server_close();worker.join()
if __name__=='__main__':unittest.main()
