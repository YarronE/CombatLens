"""Whole-game contracts use only synthetic tables and sources."""
import json,sys,tempfile,unittest,threading,copy
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from combatlens.orchestrator import demo,save_json
from combatlens.runtime.repository import Repository,Config,digest
from combatlens.runtime.game_study import GameStudy
from combatlens.runtime.validation import WorkbenchError
from combatlens.runtime.server import create_server

class GameStudyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.run=Path(demo(self.root)['research_dir']);self.path=self.run/'synthetic-source.json'
  self.data={'items':[{'id':10,'fields':{'value':0,'flag':False,'unknown':None,'effect':7,'pool':9}},{'id':10,'fields':{'value':2,'effect':8}}],'effects':[{'id':7,'fields':{'value':3}},{'id':7,'fields':{'value':4}},{'id':8,'fields':{'value':5}}],'pools':[{'id':9,'fields':{'candidate':7}},{'id':9,'fields':{'candidate':8}}],'points':[{'id':0,'fields':{'group':1,'x':0,'z':2}},{'id':1,'fields':{'group':2,'x':100,'z':100}},{'id':2,'fields':{'group':1,'x':1,'z':3}}],'description':'Synthetic lifecycle'}
  self.path.write_text(json.dumps(self.data),encoding='utf-8');package=json.loads((self.run/'research-package.json').read_text(encoding='utf-8'));package['sources'][0]['sha256']=digest(self.path.read_bytes());save_json(self.run/'research-package.json',package);fp=digest((self.run/'research-package.json').read_bytes());t=json.loads((self.run/'timelines.json').read_text(encoding='utf-8'));t['package_fingerprint']=fp;save_json(self.run/'timelines.json',t)
  self.tables=[{'id':name,'label':name,'system_id':'preparation','source_id':'synthetic-source','pointer':'/'+name,'count':len(self.data[name]),'display_fields':['value','flag','unknown'],'references':[]} for name in ['items','effects','pools','points']]
  self.tables[0]['references']=[{'table':'effects','fields':['effect']},{'table':'pools','fields':['pool'],'mode':'pool'}];self.tables[3]['projection']={'x':'x','y':'z','frame_fields':['group'],'note':'Native units only'}
  self.overlay={'schema':'combatlens-game-study/1','game_build':'synthetic-build','package_fingerprint':fp,'systems':[{'id':'preparation','label':'Preparation'}],'tables':self.tables,'lifecycle':[{'id':'start','title':'Start','system_id':'preparation','source_id':'synthetic-source','pointer':'/description'}]};self.save();self.repo=Repository(Config(self.root,research_dir=self.run));self.service=GameStudy(self.repo)
 def save(self):save_json(self.run/'game-study.json',self.overlay)
 def tearDown(self):self.tmp.cleanup()
 def test_metadata_and_legacy_missing(self):
  d=self.service.metadata();self.assertEqual(d['status'],'ready');self.assertEqual(d['lifecycle'][0]['evidence'],'Synthetic lifecycle');(self.run/'game-study.json').unlink();self.assertEqual(self.service.metadata()['status'],'missing')
 def test_physical_identity_zero_false_unknown_and_pagination(self):
  d=self.service.rows({'table':['items'],'limit':['1']});self.assertEqual(d['total'],2);r=d['rows'][0];self.assertEqual(r['ordinal'],0);self.assertEqual(r['fields']['value'],0);self.assertIs(r['fields']['flag'],False);self.assertIsNone(r['fields']['unknown']);self.assertEqual(self.service.rows({'table':['items'],'offset':['1']})['rows'][0]['ordinal'],1)
 def test_duplicate_native_ids_never_collapse(self):
  rows=self.service.rows({'table':['items'],'native_id':['10']})['rows'];self.assertEqual([r['ordinal'] for r in rows],[0,1]);record=self.service.record({'table':['items'],'ordinal':['0']});self.assertEqual(record['references'][0]['status'],'ambiguous');self.assertEqual(record['references'][0]['count'],2)
 def test_candidate_pools_are_not_applied_effects(self):
  r=self.service.record({'table':['items'],'ordinal':['0']})['references'][1];self.assertEqual(r['status'],'pool');self.assertEqual(r['ordinals'],[0,1]);self.assertNotIn('probability',r)
 def test_unique_reference_and_missing_are_explicit(self):
  self.assertEqual(self.service.record({'table':['items'],'ordinal':['1']})['references'][0]['status'],'exact');self.tables[0]['references'][0]['table']='not_registered';self.save();self.assertEqual(self.service.record({'table':['items'],'ordinal':['1']})['references'][0]['status'],'gap')
 def test_search_includes_raw_values_without_html_execution(self):
  self.assertEqual(self.service.rows({'table':['items'],'q':['value 2']})['rows'][0]['ordinal'],1);self.assertEqual(self.service.rows({'table':['items'],'q':['<script>']})['total'],0)
 def test_changed_source_rejects_cached_content(self):
  self.service.rows({'table':['items']});self.path.write_text('{}')
  with self.assertRaises(WorkbenchError) as e:self.service.record({'table':['items'],'ordinal':['0']})
  self.assertEqual(e.exception.status,409);self.assertEqual(self.service.metadata()['tables'][0]['status'],'gap')
 def test_secondary_dependency_change_invalidates_rows(self):
  package=json.loads((self.run/'research-package.json').read_text(encoding='utf-8'));dep=self.run/'dep.json';dep.write_text('{}');package['sources'].append({'id':'dep','path':str(dep),'sha256':digest(dep.read_bytes())});save_json(self.run/'research-package.json',package);fp=digest((self.run/'research-package.json').read_bytes());t=json.loads((self.run/'timelines.json').read_text(encoding='utf-8'));t['package_fingerprint']=fp;save_json(self.run/'timelines.json',t);self.overlay['package_fingerprint']=fp;self.tables[0]['dependency_ids']=['dep'];self.save();self.service.rows({'table':['items']});dep.write_text('{"changed":1}')
  with self.assertRaises(WorkbenchError):self.service.rows({'table':['items']})
 def test_fingerprint_build_schema_and_duplicate_tables_rejected(self):
  for field in ['game_build','package_fingerprint','schema']:
   old=self.overlay[field];self.overlay[field]='other';self.save()
   with self.assertRaises(WorkbenchError):self.service.metadata()
   self.overlay[field]=old
  self.tables.append(copy.deepcopy(self.tables[0]));self.save()
  with self.assertRaises(WorkbenchError):self.service.metadata()
 def test_declared_count_and_pointer_must_match_source(self):
  self.tables[0]['count']=1;self.save()
  with self.assertRaises(WorkbenchError):self.service.rows({'table':['items']})
  self.tables[0]['count']=2;self.tables[0]['pointer']='/absent';self.save()
  with self.assertRaises(WorkbenchError):self.service.rows({'table':['items']})
 def test_hostile_query_paths_and_unbounded_requests_rejected(self):
  for q in [{'table':['../source']},{'table':['items'],'offset':['-1']},{'table':['items'],'limit':['201']},{'table':['items'],'limit':['0']},{'table':['items'],'q':['x'*241]}]:
   with self.assertRaises(WorkbenchError):self.service.rows(q)
  for ordinal in ['-1','0.5','200001','2']:
   with self.assertRaises(WorkbenchError):self.service.record({'table':['items'],'ordinal':[ordinal]})
 def test_projection_never_combines_coordinate_frames(self):
  d=self.service.projection({'table':['points']});self.assertEqual(d['frames'],['1','2']);self.assertFalse(d['points']);points=self.service.projection({'table':['points'],'frame':['1']})['points'];self.assertEqual([p['native_id'] for p in points],[0,2]);self.assertFalse(any(p['x']==100 for p in points))
 def test_projection_requires_declared_frame_and_fields(self):
  with self.assertRaises(WorkbenchError):self.service.projection({'table':['items']})
  with self.assertRaises(WorkbenchError):self.service.projection({'table':['points'],'frame':['3']})
 def test_origin_checks_and_http_rows(self):
  server=create_server(Config(self.root,research_dir=self.run),port=0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   base=f'http://127.0.0.1:{server.server_port}';self.assertEqual(json.load(urlopen(base+'/api/game-study/rows?table=items'))['total'],2)
   with self.assertRaises(HTTPError) as error:urlopen(Request(base+'/api/game-study',headers={'Origin':'https://unrelated.invalid'}))
   self.assertEqual(error.exception.code,403)
  finally:server.shutdown();server.server_close();thread.join()
 def test_freeze_keeps_overlay_and_registered_evidence_closed(self):
  from combatlens.bundle import freeze
  for folder in ['src','web']:(self.root/folder).mkdir()
  (self.root/'run.py').write_text('# synthetic');destination=self.root/'copy';freeze(self.root,self.run,destination);self.path.write_text('{}');service=GameStudy(Repository(Config(destination,research_dir=destination/'local/research/frozen')));self.assertEqual(service.rows({'table':['items']})['total'],2)

 def test_profile_counts_physical_rows_without_probabilities(self):
  self.tables[0]['profile_fields']=['value','flag','unknown'];self.save()
  result=self.service.profile({'table':['items'],'field':['value']});self.assertEqual(result['total'],2);self.assertEqual(result['distinct'],2);self.assertNotIn('probability',result);self.assertEqual({g['kind'] for g in result['groups']},{'number'})
  flags=self.service.profile({'table':['items'],'field':['flag']});self.assertEqual({g['kind'] for g in flags['groups']},{'bool','missing'})
  with self.assertRaises(WorkbenchError):self.service.profile({'table':['items'],'field':['__proto__']})
 def test_changed_support_suppresses_analyst_interpretation(self):
  self.overlay['analyses']=[{'system_id':'preparation','title':'Question','interpretation':'A possibility','validation':'Check independently','source_ids':['synthetic-source']}];self.save();self.assertEqual(self.service.metadata()['analyses'][0]['status'],'hypothesis');self.path.write_text('{}');result=self.service.metadata()['analyses'][0];self.assertEqual(result['status'],'gap');self.assertNotIn('A possibility',result['interpretation'])

 def test_distribution_filters_match_scalar_types_exactly(self):
  self.tables[0]['profile_fields']=['value','flag'];self.save();self.assertEqual(self.service.rows({'table':['items'],'q':['value=0']})['total'],1);self.assertEqual(self.service.rows({'table':['items'],'q':['flag=false']})['total'],1);self.assertEqual(self.service.rows({'table':['items'],'q':['flag=0']})['total'],0)
  with self.assertRaises(WorkbenchError):self.service.rows({'table':['items'],'q':['arbitrary=1']})

 def test_group_annotations_do_not_name_duplicate_physical_rows(self):
  from unittest.mock import patch
  with patch.object(self.service,'labels',return_value={'10':'One of several names'}):
   rows=self.service.rows({'table':['items']})['rows'];self.assertTrue(all(r['label_kind']=='ambiguous_tool_annotation' for r in rows));self.assertTrue(all(r['name']!='One of several names' for r in rows));self.assertNotEqual(rows[0]['name'],rows[1]['name'])
