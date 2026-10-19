"""Designer guidance fixtures are synthetic and contain no game data."""
import copy,hashlib,json,sys,tempfile,threading,unittest
from pathlib import Path
from urllib.request import urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from combatlens.orchestrator import demo
from combatlens.runtime.repository import Repository,Config
from combatlens.runtime.event_guide import resolve
from combatlens.runtime.server import create_server

def write(path,data):path.write_text(json.dumps(data),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class GuideTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.run=Path(demo(self.root)['research_dir']);self.repo=Repository(Config(self.root,research_dir=self.run))
  self.dep=self.run/'evidence.json';write(self.dep,{'synthetic_branch':True});self.summary=self.run/'notify-execution-summary.json'
  write(self.summary,{'schema_version':'notify-execution-summary/1','game_build':'synthetic-build','rules':[{'id':'synthetic-rule','class_path':'Synthetic.Input','execution_status':'static_cil_verified'}],'source_files':[{'path':'evidence.json','sha256':sha(self.dep)}]})
  package=json.loads((self.run/'research-package.json').read_text(encoding='utf-8'));package['sources'].append({'id':'summary-one','path':str(self.summary),'sha256':sha(self.summary)});write(self.run/'research-package.json',package)
  timeline=json.loads((self.run/'timelines.json').read_text(encoding='utf-8'));timeline['package_fingerprint']=sha(self.run/'research-package.json');write(self.run/'timelines.json',timeline)
  report=json.loads((self.run/'run-report.json').read_text(encoding='utf-8'));report['adapter']='reviewed';write(self.run/'run-report.json',report)
  folder=self.root/'local/interpretations/reviewed';folder.mkdir(parents=True);self.path=folder/'event-guide.json'
  self.guide={'schema':'combatlens-event-guide/1','game_build':'synthetic-build','execution_source':{'id':'summary-one','sha256':sha(self.summary)},'evidence_files':[{'name':'evidence.json','path':str(self.dep),'sha256':sha(self.dep)}],'entries':[{'rule_id':'synthetic-rule','title':'输入记录','effect':'记录已匹配的输入。','conditions':['已进入该事件。'],'boundary':'静态证据，不代表实机验证。','numbers':[{'label':'配置值','scope':'event','path':'Value.value','unit':'未确认'}]}]};self.save()
 def save(self):write(self.path,self.guide)
 def tearDown(self):self.tmp.cleanup()
 def test_reviewed_overlay_preserves_package_and_sanitizes_paths(self):
  before=(self.run/'research-package.json').read_bytes();result=resolve(self.repo);self.assertEqual(result['status'],'ready');self.assertEqual(result['entries'][0]['title'],'输入记录');self.assertNotIn(str(self.root),json.dumps(result));self.assertEqual(before,(self.run/'research-package.json').read_bytes());self.assertEqual(result['package_fingerprint'],sha(self.run/'research-package.json'))
 def test_missing_is_explicit_and_adapter_cannot_escape(self):
  self.path.unlink();self.assertEqual(resolve(self.repo)['status'],'missing');report=json.loads((self.run/'run-report.json').read_text(encoding='utf-8'));report['adapter']='../../outside';write(self.run/'run-report.json',report);self.assertEqual(resolve(self.repo)['status'],'missing')
 def test_build_summary_and_underlying_dependency_are_separately_verified(self):
  for change in ['build','summary','dependency']:
   with self.subTest(change=change):
    original=self.summary.read_bytes();dep=self.dep.read_bytes();g=copy.deepcopy(self.guide)
    if change=='build':self.guide['game_build']='other'
    elif change=='summary':self.summary.write_bytes(original+b' ')
    else:self.dep.write_bytes(dep+b' ')
    self.save();self.assertEqual(resolve(self.repo)['status'],'unavailable');self.summary.write_bytes(original);self.dep.write_bytes(dep);self.guide=g;self.save()
 def test_dependency_must_be_inside_existing_approved_roots(self):
  outside=self.root/'outside.json';outside.write_bytes(self.dep.read_bytes());self.guide['evidence_files'][0]['path']=str(outside);self.save();self.assertEqual(resolve(self.repo)['status'],'unavailable')
 def test_duplicate_rules_unknown_paths_and_missing_dependency_fail_closed(self):
  baseline=copy.deepcopy(self.guide)
  for change in ['duplicate','path','dependency','unknown']:
   self.guide=copy.deepcopy(baseline)
   if change=='duplicate':self.guide['entries']*=2
   elif change=='path':self.guide['entries'][0]['numbers'][0]['path']='__proto__.value'
   elif change=='dependency':self.guide['evidence_files']=[]
   else:self.guide['entries'][0]['rule_id']='not-present'
   self.save();self.assertEqual(resolve(self.repo)['status'],'unavailable')
 def test_changed_event_source_is_reported_without_disclosing_false_eligibility(self):
  (self.run/'synthetic-source.json').write_text('{"changed":true}');result=resolve(self.repo);self.assertEqual(result['status'],'ready');self.assertIn('synthetic-window',result['affected_event_ids'])
 def test_pinned_symlink_cannot_escape_selected_run(self):
  pinned=self.run/'event-guide.json'
  try:pinned.symlink_to(self.path)
  except OSError:self.skipTest('Symlink privilege unavailable')
  self.assertEqual(resolve(self.repo)['status'],'unavailable')
 def test_table_proof_dependency_is_independently_checked(self):
  table=self.run/'table.json';write(table,{'synthetic_value':3});summary=json.loads(self.summary.read_text(encoding='utf-8'));summary['rules'][0]['table_proofs']=[{'source_path':str(table),'source_sha256':sha(table)}];write(self.summary,summary)
  package=json.loads((self.run/'research-package.json').read_text(encoding='utf-8'));package['sources'][-1]['sha256']=sha(self.summary);write(self.run/'research-package.json',package);timeline=json.loads((self.run/'timelines.json').read_text(encoding='utf-8'));timeline['package_fingerprint']=sha(self.run/'research-package.json');write(self.run/'timelines.json',timeline)
  self.guide['execution_source']['sha256']=sha(self.summary);self.guide['evidence_files'].append({'name':'table/table.json#'+sha(table)[:12],'path':str(table),'sha256':sha(table)});self.save();self.assertEqual(resolve(self.repo)['status'],'ready');table.write_text('{}');self.assertEqual(resolve(self.repo)['status'],'unavailable')
 def test_loopback_endpoint_returns_reviewed_contract(self):
  server=create_server(Config(self.root,research_dir=self.run),port=0);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
  try:
   with urlopen('http://127.0.0.1:'+str(server.server_port)+'/api/event-guide') as response:self.assertEqual(json.load(response)['status'],'ready')
  finally:server.shutdown();server.server_close();worker.join()
if __name__=='__main__':unittest.main()
