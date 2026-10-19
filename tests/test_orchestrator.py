import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from combatlens.orchestrator import route,demo,analyze,configured,save_json,validate_run

class RequestTests(unittest.TestCase):
 def test_prompt_is_data_and_unknown_is_rejected(self):
  adapters=[{'id':'synthetic','aliases':['Synthetic Game']}]
  self.assertEqual(route('Synthetic Game $(anything)',adapters)['id'],'synthetic')
  with self.assertRaisesRegex(ValueError,'unavailable'):route('other game',adapters)
 def test_ambiguous_request_needs_explicit_selection(self):
  adapters=[{'id':'one','aliases':['game']},{'id':'two','aliases':['game']}]
  with self.assertRaisesRegex(ValueError,'ambiguous'):route('game',adapters)
  self.assertEqual(route('game',adapters,'two')['id'],'two')
 def test_demo_has_real_source_identity_and_unknown_preview(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);result=demo(root);self.assertEqual(result['sources'],1);self.assertEqual(result['events'],1)
   out=Path(result['research_dir']);self.assertEqual(validate_run(root,out)['fingerprint'],result['fingerprint']);self.assertFalse((out/'preview.json').exists())
 def test_failed_adapter_cannot_replace_active_run(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);demo(root);pointer=root/'local/research/active-source.json';before=pointer.read_bytes()
   adapter=root/'failure.py';adapter.write_text("def prepare(request,out):\n    raise ValueError('synthetic failure')\n")
   save_json(root/'local/config.json',{'schema':'combatlens-config/1','adapters':[{'id':'broken','aliases':['game'],'entrypoint':str(adapter)}]})
   with self.assertRaisesRegex(ValueError,'synthetic failure'):analyze('game',root)
   self.assertEqual(pointer.read_bytes(),before)
   reports=[json.loads(p.read_text()) for p in (root/'local/research').glob('*/run-report.json')];self.assertTrue(any(x['state']=='failed' for x in reports))
 def test_changed_source_fails_before_activation(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);result=demo(root);out=Path(result['research_dir']);(out/'synthetic-source.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'source_validation_failed'):validate_run(root,out)

if __name__=='__main__':unittest.main()
