"""Deterministic request routing and immutable run preparation."""
from __future__ import annotations
import hashlib, importlib.util, json, os, shutil, tempfile, uuid
from datetime import datetime, timezone
from pathlib import Path
from .runtime.repository import Config, Repository
from .runtime.validation import WorkbenchError

ROOT=Path(__file__).resolve().parents[2]

def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))

def save_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    fd,temporary=tempfile.mkstemp(prefix='.pending-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if Path(temporary).exists():Path(temporary).unlink()

def configured(root=ROOT):
    path=root/'local/config.json'
    data=load_json(path) if path.is_file() else {'schema':'combatlens-config/1','adapters':[]}
    if data.get('schema')!='combatlens-config/1' or not isinstance(data.get('adapters'),list):raise ValueError('Unsupported adapter registry')
    return data

def route(prompt,adapters,adapter_id=None):
    if not isinstance(prompt,str) or not prompt.strip():raise ValueError('A research request is required')
    matches=[item for item in adapters if item.get('id')==adapter_id] if adapter_id else [item for item in adapters if any(alias.casefold() in prompt.casefold() for alias in item.get('aliases',[]) if isinstance(alias,str) and alias)]
    if len(matches)!=1:raise ValueError('adapter_ambiguous' if matches else 'adapter_unavailable: register a reviewed local adapter or use demo')
    return matches[0]

def validate_run(root,out):
    repo=Repository(Config(root,research_dir=out))
    package,fingerprint=repo.research();timeline=repo.timelines(fingerprint)
    states=repo.validity(timeline['objects'])
    if states['stale_source_ids']:raise ValueError('source_validation_failed: '+str(len(states['stale_source_ids']))+' source(s) are unavailable or changed')
    ids=[obj['id'] for obj in timeline['objects']]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate_object_id')
    return {'fingerprint':fingerprint,'sources':len(package['sources']),'objects':len(ids),'sequences':sum(len(obj.get('sequences',[])) for obj in timeline['objects']),'events':sum(len(seq.get('events',[])) for obj in timeline['objects'] for seq in obj.get('sequences',[]))}

def analyze(prompt,root=ROOT,adapter_id=None):
    adapter=route(prompt,configured(root)['adapters'],adapter_id)
    module_path=Path(adapter['entrypoint']).resolve()
    if not module_path.is_file() or module_path.suffix!='.py':raise ValueError('adapter_entrypoint_missing')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
    out=root/'local/research'/run_id;out.mkdir(parents=True,exist_ok=False)
    job={'schema':'combatlens-run/1','id':run_id,'prompt':prompt,'adapter':adapter['id'],'state':'preparing','started_at':datetime.now(timezone.utc).isoformat()}
    save_json(out/'run-report.json',job)
    try:
        spec=importlib.util.spec_from_file_location('combatlens_local_'+uuid.uuid4().hex,module_path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=module.prepare({'prompt':prompt,'config':adapter.get('config',{}),'project_root':str(root)},out)
        if not isinstance(result,dict):raise ValueError('adapter_result_must_be_object')
        job.update(result);job.update(validate_run(root,out));job['state']='ready';job['completed_at']=datetime.now(timezone.utc).isoformat()
        save_json(out/'run-report.json',job)
        summary=['# '+str(job.get('title','Combat research')),'',str(job.get('operation','Prepared research')),'','## Coverage','']
        summary.extend('- '+str(value) for value in job.get('coverage',[]));summary+=['','## Gaps',''];summary.extend('- '+str(value) for value in job.get('gaps',[]))
        (out/'analysis.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
        # A partial run never replaces this pointer.
        save_json(root/'local/research/active-source.json',{'schema_version':'research-pointer/1','relative_directory':run_id})
        return job|{'research_dir':str(out),'markdown':str(out/'analysis.md')}
    except BaseException as error:
        job['state']='cancelled' if isinstance(error,KeyboardInterrupt) else 'failed';job['error']=type(error).__name__+': '+str(error);save_json(out/'run-report.json',job)
        raise

def demo(root=ROOT):
    run_id='synthetic-'+uuid.uuid4().hex[:8];out=root/'local/research'/run_id;out.mkdir(parents=True)
    sample=out/'synthetic-source.json';save_json(sample,{'kind':'synthetic-only','window':[0.3,0.6]})
    sha=hashlib.sha256(sample.read_bytes()).hexdigest()
    package={'schema_version':1,'game':{'name':'Synthetic demo','version':'demo'},'sources':[{'id':'synthetic-source','path':str(sample),'sha256':sha}],'objects':[],'relations':[],'claims':[]}
    save_json(out/'research-package.json',package);fp=hashlib.sha256((out/'research-package.json').read_bytes()).hexdigest()
    timeline={'schema_version':'timeline-source/1','game_build':'synthetic-build','package_fingerprint':fp,'objects':[{'id':'synthetic-character','role':'character','name':'合成演示角色','mapping_status':'synthetic','sequences':[{'id':'synthetic-action','action_id':101,'name':'合成动作','duration':1.0,'unit':'seconds','source_ids':['synthetic-source'],'origin':{'kind':'synthetic','source_ids':['synthetic-source']},'events':[{'id':'synthetic-window','label':'合成窗口','kind':'interval','track':'合成事件','start':0.3,'end':0.6,'unit':'seconds','raw_unit':'seconds','timing_status':'synthetic','raw_value':{'window':[0.3,0.6]},'source_ids':['synthetic-source'],'locator':{'field':'window'},'analysis_override':None}]}],'graph':{'nodes':[],'edges':[]}}]}
    save_json(out/'timelines.json',timeline);save_json(out/'source-root.json',{'root':str(out)})
    report={'schema':'combatlens-run/1','id':run_id,'title':'合成演示','state':'ready','operation':'synthetic-demo','coverage':['对象、来源、时间区间与研究副本'],'gaps':['没有游戏数据或真实模型；此演示不证明游戏兼容性'],'findings':[]}|validate_run(root,out)
    save_json(out/'run-report.json',report);save_json(root/'local/research/active-source.json',{'schema_version':'research-pointer/1','relative_directory':run_id})
    return report|{'research_dir':str(out)}
