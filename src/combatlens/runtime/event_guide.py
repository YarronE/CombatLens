"""Reviewed explanation overlays, bound to unchanged research and underlying evidence."""
import hashlib,json,math,re
from pathlib import Path
from .validation import WorkbenchError

SHA=re.compile(r'^[a-f0-9]{64}$')
PATH=re.compile(r'^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*$')
def load(path,limit):
    if path.stat().st_size>limit:raise ValueError('解释文件超过读取上限。')
    raw=path.read_bytes()
    return json.loads(raw.decode('utf-8'),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('解释含非有限数值。'))),raw

def text(value,maximum=1200):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum:raise ValueError('解释文字字段无效。')
    return value

def field_path(value):
    if not isinstance(value,str) or not PATH.fullmatch(value) or any(p in {'__proto__','constructor','prototype'} for p in value.split('.')):raise ValueError('数值或条件路径无效。')
    return value

def entry(value,known):
    if not isinstance(value,dict) or value.get('rule_id') not in known:raise ValueError('解释没有对应执行规则。')
    result={key:text(value.get(key)) for key in ['rule_id','title','effect','boundary']}
    conditions=value.get('conditions',[])
    if not isinstance(conditions,list) or not conditions or len(conditions)>8:raise ValueError('解释需要明确条件。')
    result['conditions']=[text(item) for item in conditions]
    numbers=value.get('numbers',[])
    if not isinstance(numbers,list) or len(numbers)>12:raise ValueError('数值登记无效。')
    result['numbers']=[]
    for item in numbers:
        if not isinstance(item,dict) or item.get('scope') not in ['rule','event']:raise ValueError('数值没有明确原始来源。')
        result['numbers'].append({'label':text(item.get('label'),100),'scope':item['scope'],'path':field_path(item.get('path')),'unit':text(item.get('unit','未确认'),100),'note':text(item.get('note','来源原值'),500)})
    if 'action_id' in value:
        if type(value['action_id']) is not int:raise ValueError('Action ID 必须是原始整数。')
        result['action_id']=value['action_id']
    required=value.get('required_values',{})
    if not isinstance(required,dict) or len(required)>20:raise ValueError('实例条件无效。')
    for key,val in required.items():
        field_path(key)
        if not isinstance(val,(str,int,float,bool)) or isinstance(val,float) and not math.isfinite(val):raise ValueError('实例条件必须是已知原值。')
    result['required_values']=required
    return result

def resolve(repository):
    freshness={}
    try:
        timeline=repository.timelines();validity=repository.validity(timeline['objects'])
        freshness={'game_build':timeline['game_build'],'package_fingerprint':validity['current_package_fingerprint'],'affected_event_ids':validity['affected_event_ids']}
        report=repository.research_dir/'run-report.json'
        report=load(report,256000)[0] if report.is_file() else {}
        adapter=report.get('adapter','') if isinstance(report,dict) else ''
        local=(repository.root/'local/interpretations').resolve();pinned=repository.research_dir/'event-guide.json'
        path=pinned if pinned.is_file() else local/adapter/'event-guide.json' if isinstance(adapter,str) and re.fullmatch(r'[A-Za-z0-9_-]+',adapter) else None
        if path is None or not path.is_file():return {**freshness,'status':'missing','entries':[]}
        allowed=repository.research_dir.resolve() if path==pinned else local
        if not path.resolve().is_relative_to(allowed):raise ValueError('解释文件越过登记目录。')
        guide,raw=load(path,256000)
        if not isinstance(guide,dict) or guide.get('schema')!='combatlens-event-guide/1':raise ValueError('解释格式未支持。')
        timeline=repository.timelines();build=timeline['game_build']
        if guide.get('game_build')!=build:raise ValueError('解释与当前Build不符。')
        source=guide.get('execution_source',{});records=repository.registry();sid=source.get('id') if isinstance(source,dict) else None
        if sid not in records or not SHA.fullmatch(source.get('sha256','')) or records[sid]['expected_sha256']!=source['sha256']:raise ValueError('执行摘要登记或摘要值不符。')
        source_path=repository.source_path(records[sid]);summary,summary_raw=load(source_path,2*1024*1024)
        if hashlib.sha256(summary_raw).hexdigest()!=source['sha256']:raise ValueError('执行摘要已经变化。')
        if summary.get('schema_version')!='notify-execution-summary/1' or summary.get('game_build')!=build or not isinstance(summary.get('rules'),list):raise ValueError('执行摘要格式或Build不符。')
        files=summary.get('source_files',[]);declared=guide.get('evidence_files',[])
        if isinstance(files,list):
            files=list(files);names={item.get('path') for item in files if isinstance(item,dict)}
            for rule in summary['rules']:
                for proof in rule.get('table_proofs',[]):
                    digest=proof.get('source_sha256');table_path=proof.get('source_path')
                    if not isinstance(table_path,str) or not isinstance(digest,str) or not SHA.fullmatch(digest):raise ValueError('表格证据缺少来源摘要。')
                    name='table/'+Path(table_path).name+'#'+digest[:12]
                    if name not in names:files.append({'path':name,'sha256':digest});names.add(name)

        if not isinstance(files,list) or not files or len(files)>128 or not isinstance(declared,list):raise ValueError('执行摘要缺少可核验的依赖。')
        by_name={f.get('name'):f for f in declared if isinstance(f,dict)}
        if len(by_name)!=len(declared) or len({f.get('path') for f in files})!=len(files) or set(by_name)!={f.get('path') for f in files}:raise ValueError('解释依赖登记不完整或重复。')
        dependencies=[]
        for item in files:
            name=item.get('path');proof=by_name.get(name)
            if not isinstance(name,str) or not proof or not SHA.fullmatch(item.get('sha256','')) or proof.get('sha256')!=item['sha256']:raise ValueError('解释依赖与摘要不符。')
            record={**records[sid],'path_text':proof.get('path'),'expected_sha256':item['sha256']}
            if repository.source_status(record)['status']!='current':raise ValueError('底层证据缺失或已经变化。')
            dependencies.append({'name':name,'sha256':item['sha256']})
        known={r.get('id') for r in summary['rules'] if isinstance(r,dict)}
        values=guide.get('entries')
        if not isinstance(values,list) or len(values)>128:raise ValueError('解释条目无效。')
        entries=[entry(v,known) for v in values]
        if len({v['rule_id'] for v in entries})!=len(entries):raise ValueError('解释条目重复。')
        validity=repository.validity(timeline['objects'])
        return {'status':'ready','schema':guide['schema'],'game_build':build,'package_fingerprint':validity['current_package_fingerprint'],'execution_source':{'id':sid,'sha256':source['sha256']},'guide_sha256':hashlib.sha256(raw).hexdigest(),'dependencies':dependencies,'entries':entries,'affected_event_ids':validity['affected_event_ids']}
    except (OSError,ValueError,TypeError,KeyError,AttributeError,WorkbenchError):
        return {**freshness,'status':'unavailable','entries':[],'diagnostic':'解释证据未通过核验，请展开原始数据核对。'}
