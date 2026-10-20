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
   reports=[json.loads(p.read_text(encoding="utf-8")) for p in (root/'local/research').glob('*/run-report.json')];self.assertTrue(any(x['state']=='failed' for x in reports))
 def test_batch_can_prepare_a_valid_run_without_publishing_it(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);initial=demo(root);original=Path(initial['research_dir']);pointer=root/'local/research/active-source.json';before=pointer.read_bytes()
   adapter=root/'prepared.py';adapter.write_text("import shutil\nfrom pathlib import Path\ndef prepare(request,out):\n    source=Path("+repr(str(original))+")\n    for name in ['research-package.json','timelines.json','source-root.json']:shutil.copyfile(source/name,out/name)\n    return {'title':'Synthetic batch'}\n")
   save_json(root/'local/config.json',{'schema':'combatlens-config/1','adapters':[{'id':'prepared','aliases':['game'],'entrypoint':str(adapter)}]})
   result=analyze('game',root,activate=False);self.assertEqual(result['state'],'ready');self.assertEqual(pointer.read_bytes(),before)
   published=analyze('game',root);self.assertEqual(json.loads(pointer.read_text())['relative_directory'],published['id'])

 def test_changed_source_fails_before_activation(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);result=demo(root);out=Path(result['research_dir']);(out/'synthetic-source.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'source_validation_failed'):validate_run(root,out)

 def test_start_reuses_recorded_service_even_if_default_port_is_free(self):
  import threading
  from unittest.mock import patch
  from combatlens import cli
  from combatlens.runtime.repository import Config,Repository
  from combatlens.runtime.server import WorkbenchServer
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);result=demo(root);out=Path(result['research_dir'])
   server=WorkbenchServer(('127.0.0.1',0),Repository(Config(root,research_dir=out)));server.RequestHandlerClass=cli.LensHandler
   worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
   try:
    save_json(out/'service.json',{'port':server.server_port})
    with patch.object(cli,'ROOT',root),patch.object(cli.subprocess,'Popen') as spawn:
     service=cli.start(out,port=1)
     self.assertEqual(service['status'],'reused');self.assertIn(str(server.server_port),service['url']);spawn.assert_not_called()
   finally:server.shutdown();server.server_close();worker.join(timeout=2)

if __name__=='__main__':unittest.main()
