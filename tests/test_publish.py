import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from check_publish import check
class PublishTests(unittest.TestCase):
 def test_case_paths_and_asset_payloads_are_rejected(self):
  self.assertEqual(len(check(["local/report.json","cases/input.json","models/mesh.glb"])),3)
 def test_generic_source_is_accepted(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/"tool.py").write_text("print(1)");self.assertEqual(check(["tool.py"],root),[])
