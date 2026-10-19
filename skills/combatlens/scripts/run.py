"""Portable launcher; installation bindings remain local to each machine."""
from pathlib import Path
import argparse,json,os,subprocess,sys
parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--root',type=Path);args,remaining=parser.parse_known_args()
binding=Path(__file__).resolve().parents[1]/'local-binding.json'
root=args.root or (Path(os.environ['COMBATLENS_ROOT']) if os.environ.get('COMBATLENS_ROOT') else None)
if root is None and binding.exists():root=Path(json.loads(binding.read_text(encoding='utf-8'))['root'])
if root is None:root=next((p for p in Path(__file__).resolve().parents if (p/'src/combatlens/cli.py').is_file()),None)
if root is None:raise SystemExit('Locate CombatLens with --root or COMBATLENS_ROOT')
raise SystemExit(subprocess.call([sys.executable,str(root/'run.py'),*remaining],cwd=root))
