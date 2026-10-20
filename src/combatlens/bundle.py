"""Explicit private snapshots. Never publish these generated directories."""
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
from .orchestrator import validate_run,load_json,save_json
from .runtime.repository import Repository,Config
from .runtime.preview import PreviewRepository
from .runtime.event_guide import resolve as resolve_guide
from .runtime.presentation import resolve as resolve_theme

def sha(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()

def freeze(root,research,destination,attachments=()):
    root=Path(root).resolve();research=Path(research).resolve();destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Snapshot destination already exists; choose a new version.')
    if root==destination or root.is_relative_to(destination):raise ValueError('Snapshot cannot contain its source workspace.')
    validation=validate_run(root,research);repo=Repository(Config(root,research_dir=research))
    previews=PreviewRepository(repo);manifest=previews.manifest();response=previews.response()
    if any(a.get('status')=='ready' and b.get('status')!='ready' for a,b in zip(manifest['assets'],response['assets'])):raise ValueError('A registered preview failed validation.')
    guide=resolve_guide(repo);theme,hero=resolve_theme(repo)
    if guide['status']=='unavailable' or theme['status']=='unavailable':raise ValueError('Reviewed guide or presentation is invalid.')
    registry=repo.registry();fingerprint=validation['fingerprint'];build=repo.timelines()['game_build']
    extra=[Path(p).resolve() for p in attachments]
    if any(not p.is_file() or p.stat().st_size>16*1024*1024 for p in extra):raise ValueError('Acceptance attachments must be existing files up to 16 MiB.')
    destination.mkdir(parents=True,exist_ok=False)
    receipt={'schema':'combatlens-local-bundle/1','state':'incomplete','created_at':datetime.now(timezone.utc).isoformat(),'private':True,'fixed_installation':str(destination),'source_package_fingerprint':fingerprint,'game_build':build}
    save_json(destination/'bundle.json',receipt)
    try:
        for name in ['run.py','pyproject.toml','LICENSE','THIRD_PARTY_NOTICES.md','UPSTREAM.json']:
            if (root/name).is_file():shutil.copy2(root/name,destination/name)
        for folder in ['src','web']:
            shutil.copytree(root/folder,destination/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        out=destination/'local/research/frozen';out.mkdir(parents=True)
        for name in ['research-package.json','timelines.json','run-report.json','analysis.md','build-label.json']:
            if (research/name).is_file():shutil.copy2(research/name,out/name)
        evidence=destination/'local/evidence';evidence.mkdir()
        def copy_proof(path,expected):
            if sha(path)!=expected:raise ValueError('Evidence changed while snapshotting.')
            target=evidence/(expected+path.suffix.lower())
            if not target.exists():shutil.copy2(path,target)
            if sha(target)!=expected:raise ValueError('Snapshot evidence copy failed.')
            return target
        mapped={sid:{'path':str(copy_proof(repo.source_path(record),record['expected_sha256'])),'sha256':record['expected_sha256']} for sid,record in registry.items()}
        save_json(out/'source-root.json',{'root':str(evidence),'allowed_roots':[str(evidence)],'sources':mapped})
        preview_root=destination/'local/preview';preview_root.mkdir()
        for asset in manifest['assets']:
            if asset.get('status')!='ready':continue
            handle,_,expected=previews.open_asset(asset)
            with handle:
                target=preview_root/(expected+'.glb')
                if not target.exists():
                    with target.open('xb') as stream:shutil.copyfileobj(handle,stream)
            if sha(target)!=expected:raise ValueError('Snapshot preview copy failed.')
            asset['local_path']=target.name
        save_json(out/'preview.json',manifest)
        if guide['status']=='ready':
            pinned=research/'event-guide.json'
            original=pinned if pinned.is_file() else root/'local/interpretations'/load_json(research/'run-report.json')['adapter']/'event-guide.json'
            data=load_json(original)
            record=registry[data['execution_source']['id']]
            for item in data['evidence_files']:
                dep={**record,'path_text':item['path'],'expected_sha256':item['sha256']}
                item['path']=str(copy_proof(repo.source_path(dep),item['sha256']))
            save_json(out/'event-guide.json',data)
        if theme['status']=='ready':
            data={'schema':'combatlens-presentation/1',**{k:theme[k] for k in ['title','subtitle','palette']}}
            if hero:
                folder=destination/'local/presentations/frozen';folder.mkdir(parents=True)
                shutil.copy2(hero,folder/hero.name)
                data['hero']={**{k:theme['hero'][k] for k in ['sha256','alt','credit','source_url']},'path':'frozen/'+hero.name}
            save_json(out/'presentation.json',data)
        copies=[]
        if repo.analyses_dir.is_dir():
            for path in repo.analyses_dir.glob('*.json'):
                data=load_json(path)
                if data.get('parent_package_fingerprint')!=fingerprint or data.get('game_build')!=build:continue
                target=destination/'local/analyses'/path.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);copies.append(path.name)
        for index,path in enumerate(extra):
            target=destination/'acceptance'/f'{index:02d}-{path.name}';target.parent.mkdir(exist_ok=True);shutil.copy2(path,target)
        save_json(destination/'local/research/active-source.json',{'schema_version':'research-pointer/1','relative_directory':'frozen'})
        save_json(destination/'local/config.json',{'schema':'combatlens-config/1','adapters':[]})
        (destination/'.gitignore').write_text('*\n',encoding='utf-8')
        (destination/'LOCAL-README.md').write_text('# Private local analysis snapshot\n\nRun `python run.py start` from this directory and open the returned loopback URL.\nIncludes private evidence and saved analysis copies. Do not upload this directory.\nOriginal package bytes and source IDs are retained. Registry paths bind this fixed\nlocal installation; moving it requires rebinding and revalidation. No unpacking\nadapter, game executable, credentials or extraction keys are included.\n',encoding='utf-8')
        validation=validate_run(destination,out);frozen=Repository(Config(destination,research_dir=out))
        if guide['status']=='ready' and resolve_guide(frozen)['status']!='ready':raise ValueError('Frozen explanation dependency validation failed.')
        if any(a.get('status')=='ready' and b.get('status')!='ready' for a,b in zip(manifest['assets'],PreviewRepository(frozen).response()['assets'])):
            raise ValueError('Frozen preview validation failed.')
        try:
            git=subprocess.run(['git','-c','safe.directory='+str(root),'-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True,check=True)
            receipt['source_engine_commit']=git.stdout.strip()
        except (OSError,subprocess.CalledProcessError):receipt['source_engine_commit']=None
        files={p.relative_to(destination).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in destination.rglob('*') if p.is_file() and p.name!='bundle.json'}
        receipt.update(state='ready',validation=validation,analysis_copies=copies,guide_status=guide['status'],files=files)
        save_json(destination/'bundle.json',receipt)
        return {'state':'ready','destination':str(destination),'files':len(files),'bytes':sum(f['bytes'] for f in files.values()),'analysis_copies':len(copies),**validation}
    except BaseException as error:
        receipt.update(state='incomplete',error=type(error).__name__+': '+str(error));save_json(destination/'bundle.json',receipt);raise
