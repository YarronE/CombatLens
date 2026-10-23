"""Optional, source-bound study overlays. No game-specific rules or executable expressions."""
import hashlib
import json
import math
from .event_guide import load, text
from .validation import WorkbenchError

VIEWS={'rhythm','values','phases'}
KINDS={'configuration','observation','author_statement'}

def pointer(document,path):
    if not isinstance(path,str) or not path.startswith('/') or len(path)>2000:
        raise ValueError('字段定位无效')
    value=document
    for token in path[1:].split('/'):
        key=token.replace('~1','/').replace('~0','~')
        if key in {'__proto__','prototype','constructor'}:raise ValueError('字段定位无效')
        if isinstance(value,list):
            if not key.isdecimal() or str(int(key))!=key:raise ValueError('数组定位无效')
            value=value[int(key)]
        elif isinstance(value,dict):value=value[key]
        else:raise ValueError('字段不存在')
    return value

def number(value):
    try:return type(value) in (int,float) and math.isfinite(value)
    except OverflowError:return False

def resolve(repository):
    freshness={}
    try:
        timeline=repository.timelines()
        validity=repository.validity(timeline['objects'])
        freshness={'game_build':timeline['game_build'],'package_fingerprint':validity['current_package_fingerprint'],
                   'affected_event_ids':validity['affected_event_ids']}
        path=repository.research_dir/'design-study.json'
        if not path.is_file():return {**freshness,'status':'missing','entries':[]}
        if not path.resolve().is_relative_to(repository.research_dir.resolve()):raise ValueError('设计说明越过研究目录')
        data,raw=load(path,2*1024*1024)
        if data.get('schema')!='combatlens-design-study/1' or data.get('game_build')!=timeline['game_build'] or data.get('package_fingerprint')!=freshness['package_fingerprint']:
            raise ValueError('设计说明与研究版本不符')
        entries=data.get('entries')
        if not isinstance(entries,list) or len(entries)>500:raise ValueError('设计说明条目无效')
        registry=repository.registry();documents={};seen=set();output=[]
        contexts={(o['id'],s['id']):s for o in timeline['objects'] for s in o['sequences']}
        def source(sid):
            if sid not in registry or validity['sources'][sid]['status']!='current':raise ValueError('来源缺失或已变化')
            if sid not in documents:
                doc,content=load(repository.source_path(registry[sid]),64*1024*1024)
                if hashlib.sha256(content).hexdigest()!=registry[sid]['expected_sha256']:raise ValueError('来源已变化')
                documents[sid]=doc
            return documents[sid]
        for entry in entries:
            key=(entry.get('object_id'),entry.get('sequence_id'))
            if key not in contexts or key in seen:raise ValueError('对象或动作无效或重复')
            seen.add(key)
            result={'object_id':key[0],'sequence_id':key[1],'facts':[], 'calculations':[], 'hypotheses':[],
                    'gaps':[]}
            gaps=entry.get('gaps',[])
            if not isinstance(gaps,list):raise ValueError('证据缺口列表无效')
            result['gaps']=[text(g) for g in gaps[:30]]
            facts=entry.get('facts',[])
            if not isinstance(facts,list) or len(facts)>100:raise ValueError('事实数量无效')
            by_id={}
            for fact in facts:
                fid=text(fact.get('id'),100)
                if fid in by_id or fact.get('view') not in VIEWS or fact.get('kind','configuration') not in KINDS:raise ValueError('事实登记无效')
                item={'id':fid,'label':text(fact.get('label'),160),'view':fact['view'],'kind':fact.get('kind','configuration'),
                      'unit':fact.get('unit'),'source_id':fact.get('source_id'),'pointer':fact.get('pointer'),
                      'note':text(fact.get('note','原始配置，执行结果待确认')),'status':'gap','value':None}
                if item['unit'] is not None:item['unit']=text(item['unit'],100)
                try:
                    value=pointer(source(item['source_id']),item['pointer'])
                    deps=fact.get('dependency_ids',[])
                    if not isinstance(deps,list) or len(deps)>128:raise ValueError('依赖登记无效')
                    for sid in deps:
                        if sid not in registry or validity['sources'][sid]['status']!='current':raise ValueError('底层证据缺失或已变化')
                    if len(json.dumps(value,ensure_ascii=False,allow_nan=False))>12000:raise ValueError('字段过长，请缩小定位范围')
                    item.update(value=value,status='ready' if value is not None else 'gap',reason=None if value is not None else '原字段未知',dependency_ids=deps)
                except (ValueError,KeyError,IndexError,TypeError,OSError,WorkbenchError):item['reason']='来源、依赖或原字段未通过核验'
                by_id[fid]=item;result['facts'].append(item)
            calculations=entry.get('calculations',[])
            if not isinstance(calculations,list) or len(calculations)>30:raise ValueError('计算数量无效')
            for calc in calculations:
                inputs=calc.get('inputs',[]);item={'label':text(calc.get('label'),160),'view':calc.get('view'),'inputs':inputs,'status':'gap','value':None,'unit':None}
                if item['view'] not in VIEWS or not isinstance(inputs,list) or len(inputs)!=2 or calc.get('operation') not in {'difference','ratio'}:raise ValueError('计算登记无效')
                a,b=(by_id.get(i) for i in inputs)
                if a and b and a['status']==b['status']=='ready' and number(a['value']) and number(b['value']) and a['unit'] and a['unit'] not in {'unknown','未确认','未知'} and a['unit']==b['unit']:
                    value=a['value']-b['value'] if calc['operation']=='difference' else a['value']/b['value'] if b['value']!=0 else None
                    if number(value):item.update(status='ready',value=value,unit=a['unit'] if calc['operation']=='difference' else 'ratio')
                if item['status']=='gap':item['reason']='输入缺失、单位未确认或除数为零'
                result['calculations'].append(item)
            hypotheses=entry.get('hypotheses',[])
            if not isinstance(hypotheses,list) or len(hypotheses)>12:raise ValueError('假设数量无效')
            for h in hypotheses:
                refs=h.get('fact_ids',[])
                if h.get('view') not in VIEWS or not isinstance(refs,list) or not refs or any(i not in by_id for i in refs):raise ValueError('假设必须引用本动作的事实')
                ready=all(by_id[i]['status']=='ready' for i in refs)
                result['hypotheses'].append({'view':h['view'],'text':text(h.get('text')) if ready else '支持材料失效，暂不展示原解释',
                    'validation':text(h.get('validation')),'fact_ids':refs,'status':'hypothesis' if ready else 'gap'})
            output.append(result)
        return {**freshness,'schema':data['schema'],'status':'ready','study_sha256':hashlib.sha256(raw).hexdigest(),'entries':output}
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,OSError,WorkbenchError):
        return {**freshness,'status':'unavailable','entries':[],'diagnostic':'设计解读与当前证据未通过核验。原始工作台仍可使用。'}
