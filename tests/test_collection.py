"""Synthetic collection checks; no game data or network service dependencies."""
import hashlib,json,sys,tempfile,threading,unittest
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from combatlens.runtime.repository import Config,Repository
from combatlens.runtime.server import create_server
from combatlens.runtime.collection import Collection
from combatlens.runtime.validation import WorkbenchError
class CollectionTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.entries=[]
  for key in ['one','two']:
   folder=self.root/'local/research'/key;folder.mkdir(parents=True)
   package={'schema_version':1,'game':{'build':key},'sources':[]};raw=json.dumps(package).encode();(folder/'research-package.json').write_bytes(raw);fp=hashlib.sha256(raw).hexdigest()
   (folder/'source-root.json').write_text(json.dumps({'root':str(folder)}))
   timeline={'schema_version':'timeline-source/1','game_build':key,'package_fingerprint':fp,'objects':[{'id':key,'role':'boss','sequences':[]}]}
   (folder/'timelines.json').write_text(json.dumps(timeline));(folder/'run-report.json').write_text(json.dumps({'id':key}))
   self.entries.append({'id':key,'title':key,'directory':key,'fingerprint':fp})
  self.catalog=self.root/'local/research/one/workspaces.json';self.write_catalog();self.repo=Repository(Config(self.root,research_dir=self.catalog.parent));self.collection=Collection(self.repo)
 def tearDown(self):self.temp.cleanup()
 def write_catalog(self,entries=None):self.catalog.write_text(json.dumps({'schema_version':'workspace-collection/1','default_id':'one','entries':self.entries if entries is None else entries}))
 def test_resolves_independent_repositories(self):
  one=self.collection.resolve('one')[0];two=self.collection.resolve('two')[0]
  self.assertIsNot(one,two);self.assertEqual(one.timelines()['objects'][0]['id'],'one');self.assertEqual(two.timelines()['objects'][0]['id'],'two')
 def test_same_path_package_replacement_rejected_after_cache(self):
  self.collection.resolve('two');(self.root/'local/research/two/research-package.json').write_text('{"schema_version":1,"sources":[]}')
  with self.assertRaises(WorkbenchError) as e:self.collection.resolve('two')
  self.assertEqual(e.exception.code,'stale_workspace')
 def test_unregistered_and_unsafe_ids_rejected(self):
  for key in ['other','../one','one/two',2]:
   with self.assertRaises(WorkbenchError):self.collection.resolve(key)
 def test_invalid_entries_and_paths_rejected(self):
  for field,value in [('directory','../escape'),('directory','E:/arbitrary'),('directory','one\\..\\two'),('id',4),('fingerprint',3),('title',None)]:
   entries=json.loads(json.dumps(self.entries));entries[1][field]=value;self.write_catalog(entries)
   with self.assertRaises(WorkbenchError):self.collection.entries()
  self.write_catalog(self.entries+[self.entries[0]])
  with self.assertRaises(WorkbenchError):self.collection.entries()
 def test_absent_catalog_is_legacy(self):
  self.catalog.unlink();self.assertEqual(self.collection.response()['entries'],[])
 def test_catalog_size_budget(self):
  self.catalog.write_text(' '*524289)
  with self.assertRaises(WorkbenchError):self.collection.entries()
 def test_http_scoped_routes_and_original_host_checks(self):
  server=create_server(Config(self.root,research_dir=self.catalog.parent),port=0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
  try:
   for key in ['two','one','two']:
    with urlopen(base+'/workspaces/'+key+'/api/timelines') as r:self.assertEqual(json.load(r)['objects'][0]['id'],key)
    with urlopen(base+'/workspaces/'+key+'/api/run') as r:self.assertEqual(json.load(r)['id'],key)
   with urlopen(base+'/api/workspaces') as r:self.assertEqual(len(json.load(r)['entries']),2)
   with urlopen(base+'/api/timelines') as r:self.assertEqual(json.load(r)['objects'][0]['id'],'one')
   with self.assertRaises(HTTPError) as e:urlopen(Request(base+'/workspaces/two/api/timelines',headers={'Origin':'https://example.com'}))
   self.assertEqual(e.exception.code,403)
   with self.assertRaises(HTTPError) as e:urlopen(base+'/workspaces/missing/api/timelines')
   self.assertEqual(e.exception.code,404)
  finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
