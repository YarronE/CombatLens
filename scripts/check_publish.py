"""Check the exact distributable/staged file set, excluding local case material."""
import argparse,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(paths,root=ROOT):
 denied=[];asset={'.pak','.uasset','.uexp','.ubulk','.utoc','.ucas','.glb','.fbx','.hkx','.dll','.exe','.acf','.pem'}
 settings=root/'local/publish-denylist.json';words=json.loads(settings.read_text(encoding='utf-8')).get('words',[]) if settings.exists() else []
 for name in paths:
  relative=Path(name)
  if relative.is_absolute() or '..' in relative.parts or relative.parts[0] in ['local','cases','decompiled'] or relative.suffix.lower() in asset:denied.append(name+': excluded path');continue
  path=root/relative
  if not path.is_file():continue
  raw=path.read_bytes()
  if len(raw)>8*1024*1024:denied.append(name+': size budget');continue
  if 'vendor' in relative.parts:continue
  try:text=raw.decode('utf-8')
  except UnicodeDecodeError:denied.append(name+': unreviewed binary');continue
  if any(word.casefold() in text.casefold() for word in words):denied.append(name+': local case marker')
  if re.search('gh'+'p_'+r'[A-Za-z0-9]{30,}',text) or re.search('github'+'_pat_'+r'[A-Za-z0-9_]{30,}',text):denied.append(name+': credential pattern')
 return denied
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--staged',action='store_true');args=parser.parse_args()
 command=['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),'diff','--cached','--name-only','--diff-filter=ACMR','-z'] if args.staged else ['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),'ls-files','--cached','--others','--exclude-standard','-z']
 result=subprocess.run(command,capture_output=True,check=True);paths=[p for p in result.stdout.decode().split(chr(0)) if p];denied=check(paths)
 print(json.dumps({'files_checked':len(paths),'rejected':denied},ensure_ascii=False,indent=2));return bool(denied)
if __name__=='__main__':raise SystemExit(main())
