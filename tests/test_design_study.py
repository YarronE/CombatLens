import copy,json,sys,tempfile,unittest,threading
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from combatlens.orchestrator import demo
from combatlens.runtime.repository import Repository,Config,digest
from combatlens.runtime.design_study import resolve,pointer
from combatlens.runtime.server import create_server

class StudyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.run=Path(demo(self.root)['research_dir']);self.repo=Repository(Config(self.root,research_dir=self.run))
  self.evidence=self.run/'synthetic-source.json';self.evidence.write_text(json.dumps({'zero':0,'flag':False,'dynamic':{'parameter':'runtime'},'unknown':None,'a':4,'b':2}),encoding='utf-8')
  package=json.loads((self.run/'research-package.json').read_text());package['sources'][0]['sha256']=digest(self.evidence.read_bytes());self.write('research-package.json',package)
  timeline=json.loads((self.run/'timelines.json').read_text());timeline['package_fingerprint']=digest((self.run/'research-package.json').read_bytes());self.write('timelines.json',timeline)
  self.entry={'object_id':'synthetic-character','sequence_id':'synthetic-action','facts':[{'id':k,'label':k,'view':'values','source_id':'synthetic-source','pointer':'/'+k,'unit':'raw'} for k in ['zero','flag','dynamic','unknown','a','b']], 'calculations':[{'label':'difference','view':'values','operation':'difference','inputs':['a','b']}], 'hypotheses':[{'view':'values','text':'A reviewable possibility','validation':'Check the runtime branch','fact_ids':['a']}], 'gaps':['No game runtime evidence']}
  self.study={'schema':'combatlens-design-study/1','game_build':'synthetic-build','package_fingerprint':timeline['package_fingerprint'],'entries':[self.entry]};self.save()
 def write(self,name,value):(self.run/name).write_text(json.dumps(value),encoding='utf-8')
 def save(self):self.write('design-study.json',self.study)
 def tearDown(self):self.tmp.cleanup()
 def test_zero_false_dynamic_unknown_stay_distinct(self):
  r=resolve(self.repo);self.assertEqual(r['status'],'ready');v={f['id']:f for f in r['entries'][0]['facts']};self.assertEqual(v['zero']['value'],0);self.assertIs(v['flag']['value'],False);self.assertIsInstance(v['dynamic']['value'],dict);self.assertEqual(v['unknown']['status'],'gap')
 def test_source_change_invalidates_facts_calculation_hypothesis(self):
  self.evidence.write_text('{}');r=resolve(self.repo);e=r['entries'][0];self.assertTrue(all(f['status']=='gap' for f in e['facts']));self.assertEqual(e['calculations'][0]['status'],'gap');self.assertEqual(e['hypotheses'][0]['status'],'gap');self.assertIn('synthetic-window',r['affected_event_ids'])
 def test_wrong_build_and_package_fail_closed(self):
  for k in ['game_build','package_fingerprint']:
   old=self.study[k];self.study[k]='other';self.save();self.assertEqual(resolve(self.repo)['status'],'unavailable');self.study[k]=old
 def test_object_sequence_and_fact_ids_are_scoped(self):
  self.entry['object_id']='other';self.save();self.assertEqual(resolve(self.repo)['status'],'unavailable');self.entry['object_id']='synthetic-character';self.entry['facts'].append(copy.deepcopy(self.entry['facts'][0]));self.save();self.assertEqual(resolve(self.repo)['status'],'unavailable')
 def test_unknown_units_boolean_inputs_zero_denominator_not_computed(self):
  for pair in [['a','zero'],['a','flag'],['a','dynamic']]:
   self.entry['calculations'][0].update(operation='ratio',inputs=pair);self.save();self.assertEqual(resolve(self.repo)['entries'][0]['calculations'][0]['status'],'gap')
  self.entry['calculations'][0].update(operation='ratio',inputs=['a','b']);self.entry['facts'][-1]['unit']=None;self.save();self.assertEqual(resolve(self.repo)['entries'][0]['calculations'][0]['status'],'gap')
 def test_bounded_calculations_and_provenance(self):
  r=resolve(self.repo);self.assertEqual(r['entries'][0]['calculations'][0]['value'],2);self.assertEqual(r['entries'][0]['facts'][0]['pointer'],'/zero');self.assertNotIn(str(self.root),json.dumps(r))
 def test_missing_or_forbidden_pointer_is_gap(self):
  for p in ['/absent','/__proto__/a','/a/-1']:
   self.entry['facts'][0]['pointer']=p;self.save();self.assertEqual(resolve(self.repo)['entries'][0]['facts'][0]['status'],'gap')
 def test_secondary_dependency_is_required(self):
  self.entry['facts'][0]['dependency_ids']=['not-registered'];self.save();self.assertEqual(resolve(self.repo)['entries'][0]['facts'][0]['status'],'gap')
 def test_old_packages_work_without_overlay(self):
  (self.run/'design-study.json').unlink();self.assertEqual(resolve(self.repo)['status'],'missing');self.assertEqual(self.repo.timelines_response()['game_build'],'synthetic-build')
 def test_overlay_cannot_follow_external_symlink(self):
  outside=self.root/'external.json';outside.write_text(json.dumps(self.study));(self.run/'design-study.json').unlink()
  try:(self.run/'design-study.json').symlink_to(outside)
  except OSError:self.skipTest('Symlink unavailable')
  self.assertEqual(resolve(self.repo)['status'],'unavailable')
 def test_endpoint_uses_existing_origin_authorization(self):
  server=create_server(Config(self.root,research_dir=self.run),port=0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   url=f'http://127.0.0.1:{server.server_port}/api/design-study';self.assertEqual(json.load(urlopen(url))['status'],'ready')
   with self.assertRaises(HTTPError) as error:urlopen(Request(url,headers={'Origin':'https://unrelated.invalid'}))
   self.assertEqual(error.exception.code,403)
  finally:server.shutdown();server.server_close();thread.join()
 def test_pointer_escaped_keys_and_lists(self):self.assertIs(pointer({'a/b':[False]},'/a~1b/0'),False)
