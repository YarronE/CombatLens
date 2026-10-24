"""Optional designer readings with recomputed, source-bound evidence."""
import json, math
from .design_study import pointer
from .validation import WorkbenchError, json_equivalent

def text(value, limit=2000):
    if not isinstance(value,str) or len(value)>limit:raise ValueError('Reading text exceeds contract')
    return value

def strings(value,maximum=8):
    if not isinstance(value,list) or len(value)>maximum:raise ValueError('Reading list exceeds contract')
    return [text(v) for v in value]

def scalar(value):
    if value is not None and type(value) not in (str,int,float,bool):raise ValueError('Scalar required')
    if type(value) is float and not math.isfinite(value):raise ValueError('Finite scalar required')
    return value

def resolve(service,manifest):
    report=manifest.get('reading')
    if report is None:return {'status':'missing','chapters':[]}
    try:
        if not isinstance(report,dict) or report.get('schema')!='combatlens-game-reading/1':raise ValueError('Unknown reading schema')
        facts=report.get('facts');chapters=report.get('chapters')
        if not isinstance(facts,list) or not 1<=len(facts)<=96 or not isinstance(chapters,list) or not 1<=len(chapters)<=16:raise ValueError('Invalid reading size')
        registry=service.repo.registry();source_meta={s['id']:s for s in service.repo.research()[0]['sources']};tables={};resolved={}
        def table(tid):
            if tid not in tables:tables[tid]=service.table(tid,manifest)
            return tables[tid]
        for fact in facts:
            fid=text(fact.get('id'),80)
            if not fid or fid in resolved:raise ValueError('Duplicate reading fact')
            item={'id':fid,'label':text(fact.get('label'),200),'status':'gap','note':text(fact.get('note',''))}
            try:
                for sid in fact.get('dependency_ids',[]):service.current(sid,registry)
                if fact.get('type')=='excerpt':
                    sid=fact['source_id'];doc=service.document(sid,registry);value=pointer(doc,fact['pointer'])
                    if value is None or len(json.dumps(value,ensure_ascii=False,allow_nan=False))>4000:raise ValueError('Invalid excerpt')
                    item.update(value=value,kind=source_meta[sid].get('kind','source'),source={'id':sid,'sha256':registry[sid]['expected_sha256'],'pointer':fact['pointer'],'dependency_ids':fact.get('dependency_ids',[])})
                elif fact.get('type') in {'record','measure'}:
                    t,rows,reg=table(fact['table']);source={'id':t['source_id'],'sha256':reg[t['source_id']]['expected_sha256'],'pointer':t.get('pointer',''),'dependency_ids':t.get('dependency_ids',[])}
                    item.update(table=t['id'],kind='configuration',source=source)
                    if fact['type']=='record':
                        ordinal=fact['ordinal'];fields=fact['fields']
                        if type(ordinal) is not int or not 0<=ordinal<len(rows) or not isinstance(fields,list) or not 1<=len(fields)<=16:raise ValueError('Invalid record fact')
                        row=rows[ordinal];value={text(k,100):row['fields'][k] for k in fields}
                        item.update(ordinal=ordinal,native_id=row['id'],value=value)
                        source['pointer']+=('/'+str(ordinal) if not t.get('single_row') else '')+'/fields'
                    else:
                        where=fact.get('where',{});operation=fact['operation']
                        if not isinstance(where,dict) or len(where)>4 or operation not in {'count','distinct'}:raise ValueError('Invalid measure')
                        for k,v in where.items():text(k,100);scalar(v)
                        selected=[r for r in rows if all(k in r['fields'] and json_equivalent(r['fields'][k],v) for k,v in where.items()) and ('native_id' not in fact or json_equivalent(r['id'],scalar(fact['native_id'])))]
                        if operation=='count':value=len(selected)
                        else:
                            field=text(fact['field'],100);values=[scalar(r['fields'][field]) for r in selected]
                            # Preserve false, zero, null and string identity; unify numeric 1/1.0.
                            value=len({('number' if type(v) in (int,float) else type(v).__name__,json.dumps(int(v) if type(v) is float and v.is_integer() else v,ensure_ascii=False,allow_nan=False)) for v in values})
                        item.update(value=value,basis='physical_rows',scope={'operation':operation,'where':where,'native_id':fact.get('native_id'),'field':fact.get('field'),'total':len(rows)})
                else:raise ValueError('Unsupported fact type')
                if len(json.dumps(item.get('value'),ensure_ascii=False,allow_nan=False))>12000:raise ValueError('Evidence too large')
                item['status']='ready'
            except (WorkbenchError,ValueError,KeyError,TypeError,IndexError,OSError,OverflowError):
                item.pop('value',None);item['reason']='来源、底层依赖或字段未通过核验'
            resolved[fid]=item
        output=[];seen=set()
        for chapter in chapters:
            cid=text(chapter.get('id'),80);refs=chapter.get('fact_ids')
            if not cid or cid in seen or not isinstance(refs,list) or not refs or len(refs)>32 or len(set(refs))!=len(refs) or any(fid not in resolved for fid in refs):raise ValueError('Chapter support invalid')
            seen.add(cid);ready=all(resolved[fid]['status']=='ready' for fid in refs)
            item={k:text(chapter.get(k,''),200 if k in {'id','title','short_title','question'} else 2000) for k in ['id','title','short_title','question','validation']}
            item.update(status='hypothesis' if ready else 'gap',fact_ids=refs,gaps=strings(chapter.get('gaps',[])),system_ids=strings(chapter.get('system_ids',[])),evidence=[resolved[fid] for fid in refs])
            if ready:
                item.update(player_choice=text(chapter.get('player_choice','')),interpretation=strings(chapter.get('interpretation',[])),connection=text(chapter.get('connection','')),counterexamples=strings(chapter.get('counterexamples',[])))
                rows=chapter.get('tradeoffs',[])
                if not isinstance(rows,list) or len(rows)>8:raise ValueError('Tradeoff table too large')
                item['tradeoffs']=[{k:text(r.get(k,'')) for k in ['option','gain','cost','condition']} for r in rows]
            else:item['diagnostic']='支持材料失效，暂不展示依赖它的设计解读。'
            output.append(item)
        return {'status':'ready','schema':report['schema'],'title':text(report.get('title','玩法解读'),200),'scope':text(report.get('scope','')),'chapters':output}
    except (ValueError,KeyError,TypeError,AttributeError,WorkbenchError):
        return {'status':'unavailable','chapters':[],'diagnostic':'玩法解读登记未通过核验，原始配置仍可查询。'}
