"""Private bundle behavior verified only with synthetic case material."""
import json,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from combatlens.orchestrator import demo,load_json,save_json,validate_run
from combatlens.bundle import freeze

class BundleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.root=self.base/'engine';self.root.mkdir();self.run=Path(demo(self.root)['research_dir']);self.dest=self.base/'case/local/frozen'
  (self.root/'src').mkdir();(self.root/'src/readme.py').write_text('# synthetic runtime');(self.root/'web').mkdir();(self.root/'web/index.html').write_text('synthetic');(self.root/'run.py').write_text('# synthetic launcher')
 def tearDown(self):self.tmp.cleanup()
 def test_closed_evidence_exact_research_and_no_source_pointer_changes(self):
  raw=(self.run/'research-package.json').read_bytes();pointer=(self.root/'local/research/active-source.json').read_bytes();result=freeze(self.root,self.run,self.dest)
  self.assertEqual(result['state'],'ready');out=self.dest/'local/research/frozen';self.assertEqual((out/'research-package.json').read_bytes(),raw);self.assertEqual(pointer,(self.root/'local/research/active-source.json').read_bytes())
  (self.run/'synthetic-source.json').unlink();self.assertEqual(validate_run(self.dest,out)['fingerprint'],result['fingerprint'])
  receipt=load_json(self.dest/'bundle.json');self.assertTrue(receipt['private']);self.assertEqual(receipt['state'],'ready')
  for name,record in receipt['files'].items():self.assertEqual(hashlib.sha256((self.dest/name).read_bytes()).hexdigest(),record['sha256'])
 def test_destination_is_exclusive_and_stale_sources_never_export(self):
  self.dest.mkdir(parents=True);(self.dest/'keep').write_text('retained')
  with self.assertRaisesRegex(ValueError,'already exists'):freeze(self.root,self.run,self.dest)
  self.assertEqual((self.dest/'keep').read_text(),'retained');(self.run/'synthetic-source.json').write_text('{}')
  with self.assertRaisesRegex(ValueError,'source_validation_failed'):freeze(self.root,self.run,self.base/'other')
  self.assertFalse((self.base/'other').exists())
 def test_only_compatible_copies_are_included_and_credentials_excluded(self):
  fp=validate_run(self.root,self.run)['fingerprint'];folder=self.root/'local/analyses';folder.mkdir();save_json(folder/'same.json',{'game_build':'synthetic-build','parent_package_fingerprint':fp,'revision':4});save_json(folder/'foreign.json',{'game_build':'other','parent_package_fingerprint':fp})
  (self.root/'.env').write_text('synthetic secret');(self.root/'local/config.json').write_text('{"private_config":"synthetic-only"}')
  result=freeze(self.root,self.run,self.dest);self.assertEqual(result['analysis_copies'],1);self.assertEqual(load_json(self.dest/'local/analyses/same.json')['revision'],4);self.assertFalse((self.dest/'.env').exists());self.assertNotIn('private_config',(self.dest/'local/config.json').read_text())
 def test_failure_keeps_explicit_incomplete_receipt(self):
  (self.root/'web/index.html').unlink();(self.root/'web').rmdir()
  with self.assertRaises(FileNotFoundError):freeze(self.root,self.run,self.dest)
  self.assertEqual(load_json(self.dest/'bundle.json')['state'],'incomplete')
 def test_reviewed_theme_is_pinned_without_touching_inheritance(self):
  theme=self.root/'local/presentations/synthetic';theme.mkdir(parents=True);save_json(theme/'theme.json',{'schema':'combatlens-presentation/1','title':'Synthetic','palette':{'accent':'#abcdef'}})
  report=load_json(self.run/'run-report.json');report['adapter']='synthetic';save_json(self.run/'run-report.json',report)
  freeze(self.root,self.run,self.dest);self.assertEqual(load_json(self.dest/'local/research/frozen/presentation.json')['palette']['accent'],'#abcdef')

 def test_reviewed_guide_is_closed_over_copied_dependencies(self):
  import test_event_guide
  from combatlens.runtime.event_guide import resolve
  from combatlens.runtime.repository import Config,Repository
  fixture=test_event_guide.GuideTests();fixture.setUp()
  try:
   for folder in ['src','web']:(fixture.root/folder).mkdir()
   (fixture.root/'run.py').write_text('# synthetic')
   destination=self.base/'closed-guide';freeze(fixture.root,fixture.run,destination)
   fixture.dep.write_text('{}')
   repo=Repository(Config(destination,research_dir=destination/'local/research/frozen'))
   self.assertEqual(resolve(repo)['status'],'ready')
  finally:fixture.tearDown()

 def test_design_study_keeps_exact_overlay_and_closed_sources(self):
  from test_design_study import StudyTests
  from combatlens.runtime.design_study import resolve
  from combatlens.runtime.repository import Config,Repository
  fixture=StudyTests();fixture.setUp()
  try:
   for folder in ['src','web']:(fixture.root/folder).mkdir()
   (fixture.root/'run.py').write_text('# synthetic')
   raw=(fixture.run/'design-study.json').read_bytes()
   destination=self.base/'closed-study';freeze(fixture.root,fixture.run,destination)
   self.assertEqual((destination/'local/research/frozen/design-study.json').read_bytes(),raw)
   fixture.evidence.write_text('{}')
   repo=Repository(Config(destination,research_dir=destination/'local/research/frozen'))
   result=resolve(repo);self.assertEqual(result['status'],'ready')
   self.assertEqual(result['entries'][0]['calculations'][0]['value'],2)
  finally:fixture.tearDown()
