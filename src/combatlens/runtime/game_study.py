"""Bounded, read-only whole-game evidence queries over registered sources."""
import hashlib,json,re,threading
from collections import OrderedDict,Counter
from .repository import read_json
from .validation import WorkbenchError,json_equivalent
from .design_study import pointer
from .game_reading import resolve as resolve_reading

IDENTIFIER=re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
MAX_SOURCE=192*1024*1024

def fail(message,status=503):raise WorkbenchError(message,status=status,code='invalid_game_study')
def bounded_int(value,maximum,label):
    if isinstance(value,bool):fail(label+' 无效',400)
    try:n=int(value)
    except (ValueError,TypeError,OverflowError):fail(label+' 无效',400)
    if str(n)!=str(value) or not 0<=n<=maximum:fail(label+' 超出范围',400)
    return n

class GameStudy:
    def __init__(self,repository):self.repo=repository;self.lock=threading.RLock();self.cache=OrderedDict();self.bytes=0
    def manifest(self):
        path=self.repo.research_dir/'game-study.json'
        if not path.is_file():return None
        if not path.resolve().is_relative_to(self.repo.research_dir.resolve()) or path.stat().st_size>2*1024*1024:fail('全游戏研究文件越界或过大')
        d,_=read_json(path);_,fp=self.repo.research();timeline=self.repo.timelines(fp)
        if not isinstance(d,dict) or d.get('schema')!='combatlens-game-study/1' or d.get('package_fingerprint')!=fp or d.get('game_build')!=timeline['game_build']:fail('全游戏研究与来源版本不符')
        tables=d.get('tables',[]);systems=d.get('systems',[])
        if not isinstance(tables,list) or len(tables)>120 or not isinstance(systems,list) or len(systems)>30:fail('目录数量无效')
        ids=set();sysids=set()
        for s in systems:
            if not isinstance(s,dict) or not IDENTIFIER.fullmatch(str(s.get('id',''))) or s['id'] in sysids:fail('系统 ID 无效')
            sysids.add(s['id'])
        registry=self.repo.registry()
        for t in tables:
            if not isinstance(t,dict) or not IDENTIFIER.fullmatch(str(t.get('id',''))) or t['id'] in ids or t.get('system_id') not in sysids or t.get('source_id') not in registry:fail('表登记无效')
            ids.add(t['id'])
            deps=t.get('dependency_ids',[]);refs=t.get('references',[])
            if type(t.get('count')) is not int or not 0<=t['count']<=200000 or not isinstance(deps,list) or any(x not in registry for x in deps) or not isinstance(refs,list) or len(refs)>100:fail('表依赖或范围无效')
            for r in refs:
                if not isinstance(r,dict) or not isinstance(r.get('fields'),list) or len(r['fields'])>128 or any(not isinstance(f,str) for f in r['fields']) or not IDENTIFIER.fullmatch(str(r.get('table',''))) or r.get('mode','reference') not in {'reference','pool'}:fail('引用登记无效')
        return d
    def current(self,sid,registry):
        if sid not in registry or self.repo.source_status(registry[sid])['status']!='current':fail('来源缺失或已变化，请重新导入研究包',409)
    def dependencies(self,t):
        registry=self.repo.registry()
        for sid in [t['source_id'],*t.get('dependency_ids',[])]:self.current(sid,registry)
        return registry
    def document(self,sid,registry):
        self.current(sid,registry);r=registry[sid];path=self.repo.source_path(r);stat=path.stat();key=(sid,r['expected_sha256'],stat.st_mtime_ns,stat.st_ctime_ns,stat.st_size)
        with self.lock:
            if key in self.cache:self.cache.move_to_end(key);return self.cache[key][0]
            if stat.st_size>MAX_SOURCE:fail('来源超过读取上限')
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=r['expected_sha256']:fail('读取期间来源变化',409)
            try:value=json.loads(raw.decode('utf-8-sig'),parse_constant=lambda _:fail('来源含非有限数字'))
            except (ValueError,UnicodeError,RecursionError):fail('来源 JSON 无效')
            # Bound resident documents by source bytes and item count.
            while self.cache and (len(self.cache)>=4 or self.bytes+len(raw)>224*1024*1024):
                _,(_,size)=self.cache.popitem(last=False);self.bytes-=size
            self.cache[key]=(value,len(raw));self.bytes+=len(raw);return value
    def table(self,tid,d=None):
        d=d or self.manifest()
        if d is None:fail('当前研究包没有全游戏研究',404)
        if not isinstance(tid,str) or not IDENTIFIER.fullmatch(tid):fail('表 ID 无效',400)
        t=next((t for t in d['tables'] if t['id']==tid),None)
        if t is None:fail('未登记该表',404)
        registry=self.dependencies(t);doc=self.document(t['source_id'],registry)
        try:rows=pointer(doc,t['pointer']) if t.get('pointer') else doc
        except (ValueError,KeyError,IndexError,TypeError):fail('表定位字段缺失')
        if isinstance(rows,dict) and t.get('single_row'):rows=[rows]
        if not isinstance(rows,list) or len(rows)!=t['count'] or any(not isinstance(r,dict) or 'id' not in r or not isinstance(r.get('fields'),dict) for r in rows):fail('表结构或物理行数与登记不符')
        t=dict(t);counts=Counter(str(r['id']) for r in rows);t['_duplicate_ids']={key for key,count in counts.items() if count>1}
        return t,rows,registry
    def labels(self,t,registry):
        sid=t.get('label_source_id')
        if not sid:return {}
        try:
            d=self.document(sid,registry)
            return {str(e['ID']):' / '.join(str(x) for x in e.get('Entries',[])[:3])[:220] for e in d.get('Entries',[]) if isinstance(e,dict) and 'ID' in e}
        except (WorkbenchError,TypeError,KeyError,AttributeError):return {}
    def summary(self,t,row,ordinal,labels):
        duplicate=str(row['id']) in t.get('_duplicate_ids',set())
        annotation=labels.get(str(row['id']))
        name=row.get('name') or (annotation if not duplicate else None) or t['label']+' '+str(row['id'])+(' · 物理行 '+str(ordinal) if duplicate else '')
        fields={k:row['fields'][k] for k in t.get('display_fields',[])[:12] if k in row['fields']}
        return {'table':t['id'],'ordinal':ordinal,'native_id':row['id'],'name':str(name)[:240],'label_kind':'source_name' if row.get('name') else 'ambiguous_tool_annotation' if duplicate and annotation else 'tool_annotation' if annotation else 'native_id','fields':fields,'build_kind':t.get('build_kind')}
    def metadata(self):
        d=self.manifest()
        if d is None:return {'status':'missing','systems':[],'tables':[],'lifecycle':[]}
        tables=[];registry=self.repo.registry()
        for t in d['tables']:
            item={k:v for k,v in t.items() if k not in {'pointer','dependency_ids','label_source_id','references'}}
            try:self.dependencies(t);item['status']='current'
            except WorkbenchError:item['status']='gap'
            tables.append(item)
        lifecycle=[]
        for step in d.get('lifecycle',[])[:20]:
            value={k:step.get(k) for k in ['id','title','system_id','source_id']}
            try:value['evidence']=pointer(self.document(step['source_id'],registry),step['pointer']);value['status']='current'
            except (WorkbenchError,ValueError,KeyError,TypeError,IndexError):value.update(status='gap',evidence='来源未通过核验')
            lifecycle.append(value)
        analyses=[]
        for a in d.get('analyses',[])[:30]:
            item={k:a.get(k) for k in ['system_id','title','validation','source_ids']}
            try:
                if not isinstance(a.get('source_ids'),list) or not a['source_ids']:raise ValueError()
                for sid in a['source_ids']:self.current(sid,registry)
                item.update(status='hypothesis',interpretation=str(a.get('interpretation',''))[:2000])
            except (WorkbenchError,ValueError,TypeError):item.update(status='gap',interpretation='支持材料已失效，暂不展示原解释。')
            analyses.append(item)
        return {'reading':resolve_reading(self,d),'analyses':analyses,'status':'ready','schema':d['schema'],'game_build':d['game_build'],'package_fingerprint':d['package_fingerprint'],'title':d.get('title','全游戏研究'),'systems':d['systems'],'tables':tables,'lifecycle':lifecycle,'build':d.get('build',{}),'gaps':d.get('gaps',[])[:40],'sources':[{'id':s['id'],'kind':s.get('kind'),'url':s.get('url'),'title':s.get('title',s['id'])} for s in self.repo.research()[0]['sources']]}
    def measure_scope(self,query,tid):
        if 'fact' not in query:return None
        values=query['fact']
        if len(values)!=1 or not isinstance(values[0],str) or not 1<=len(values[0])<=80:fail('统计依据标识无效',400)
        report=resolve_reading(self,self.manifest(),requested_fact=values[0])
        for chapter in report.get('chapters',[]):
            for fact in chapter['evidence']:
                if fact['id']!=values[0]:continue
                if fact['status']!='ready' or 'scope' not in fact or fact.get('table')!=tid:fail('统计依据或对应资料表已失效，请返回解读重新核对',409)
                return {**fact['scope'],'id':fact['id'],'label':fact['label'],'value':fact['value'],'chapter':chapter['id']}
        fail('统计依据未登记，请返回解读重新选择',409)

    def rows(self,query):
        tid=query.get('table',[''])[0];q=query.get('q',[''])[0];offset=bounded_int(query.get('offset',['0'])[0],200000,'偏移');limit=bounded_int(query.get('limit',['40'])[0],200,'条数')
        if not limit or len(q)>240:fail('查询超出范围',400)
        t,rows,registry=self.table(tid);scope=self.measure_scope(query,tid);labels=self.labels(t,registry);terms=q.casefold().split();native=query.get('native_id',[None])[0];frame=query.get('frame',[None])[0];matches=[]
        frame_fields=(t.get('projection') or {}).get('frame_fields',[])
        condition=None
        if '=' in q:
            field,value=q.split('=',1)
            if field not in t.get('profile_fields',[]):fail('筛选字段未登记',400)
            try:expected=json.loads(value)
            except (ValueError,TypeError):fail('筛选值必须是 JSON 原值',400)
            if isinstance(expected,(list,dict)):fail('筛选值必须是标量',400)
            condition=(field,expected);terms=[]
        for i,r in enumerate(rows):
            if scope:
                if any(k not in r['fields'] or not json_equivalent(r['fields'][k],v) for k,v in scope['where'].items()):continue
                if scope['has_native_id'] and not json_equivalent(r['id'],scope['native_id']):continue
            if native is not None and str(r['id'])!=native:continue
            if condition:
                key,value=condition
                if key not in r['fields'] or not json_equivalent(r['fields'][key],value):continue
            if frame is not None and '|'.join(str(r['fields'].get(k)) for k in frame_fields)!=frame:continue
            if terms:
                text=(str(r['id'])+' '+labels.get(str(r['id']),'')+' '+str(r.get('name',''))+' '+str(r['fields'])).casefold()
                if not all(term in text for term in terms):continue
            matches.append(i)
        return {'table':tid,'scope':scope,'total':len(matches),'offset':offset,'limit':limit,'rows':[self.summary(t,rows[i],i,labels) for i in matches[offset:offset+limit]],'source_id':t['source_id'],'package_fingerprint':self.repo.research()[1]}
    def record(self,query):
        tid=query.get('table',[''])[0];ordinal=bounded_int(query.get('ordinal',[''])[0],200000,'物理行');d=self.manifest();t,rows,registry=self.table(tid,d)
        if ordinal>=len(rows):fail('物理行不存在',404)
        row=rows[ordinal];result=self.summary(t,row,ordinal,self.labels(t,registry));fields=row['fields'];refs=[]
        for rule in t.get('references',[]):
            target=next((x for x in d['tables'] if x['id']==rule['table']),None)
            active=[(field,fields[field]) for field in rule['fields'] if field in fields and fields[field] not in rule.get('sentinels',[-1]) and type(fields[field]) in (int,str)]
            if not active:continue
            try:
                if target is None:raise ValueError()
                tt,rr,reg=self.table(target['id'],d);lookup={}
                for i,r in enumerate(rr):lookup.setdefault(str(r['id']),[]).append(i)
                for field,value in active:
                    hits=lookup.get(str(value),[]);refs.append({'field':field,'native_id':value,'table':rule['table'],'mode':rule.get('mode','reference'),'status':('pool' if rule.get('mode')=='pool' else 'exact' if len(hits)==1 else 'ambiguous') if hits else 'missing','count':len(hits),'ordinals':hits[:200]})
            except (WorkbenchError,ValueError):
                refs.extend({'field':f,'native_id':v,'table':rule['table'],'mode':rule.get('mode','reference'),'status':'gap','count':0,'ordinals':[]} for f,v in active)
        if len(json.dumps(fields,ensure_ascii=False,allow_nan=False))>180000:fail('该行超过详情显示上限')
        result.update(fields=fields,references=refs,source={'id':t['source_id'],'pointer':(t.get('pointer','')+'/'+str(ordinal) if not t.get('single_row') else t.get('pointer','')),'sha256':registry[t['source_id']]['expected_sha256'],'dependency_ids':t.get('dependency_ids',[])},game_build=d['game_build'],package_fingerprint=d['package_fingerprint'],note=t.get('note','原始配置；运行结果待核验'))
        return result
    def profile(self,query):
        t,rows,registry=self.table(query.get('table',[''])[0]);field=query.get('field',[''])[0]
        if field not in t.get('profile_fields',[]):fail('未登记该分布字段',400)
        groups={}
        for r in rows:
            value=r['fields'].get(field);kind=('number' if type(value) in (int,float) else type(value).__name__) if field in r['fields'] else 'missing'
            if kind not in {'str','number','bool','NoneType','missing'}:fail('复杂字段不进行分类计数',400)
            canonical_value=int(value) if type(value) is float and value.is_integer() else value
            key=(kind,json.dumps(canonical_value,ensure_ascii=False,allow_nan=False))
            if key not in groups:groups[key]={'value':value,'kind':kind,'count':0}
            groups[key]['count']+=1
        values=sorted(groups.values(),key=lambda g:-g['count'])
        return {'table':t['id'],'field':field,'total':len(rows),'distinct':len(values),'groups':values[:40],'other_rows':sum(v['count'] for v in values[40:]),'source_id':t['source_id'],'basis':'physical_rows','note':'登记物理行的分类计数，不代表掉落概率、出场率或实际可获得数量。'}
    def projection(self,query):
        t,rows,registry=self.table(query.get('table',[''])[0]);p=t.get('projection')
        if not p or not p.get('frame_fields') or not isinstance(p.get('x'),str) or not isinstance(p.get('y'),str):fail('该表没有已登记的坐标投影',400)
        frames=sorted(set('|'.join(str(r['fields'].get(k)) for k in p['frame_fields']) for r in rows));frame=query.get('frame',[None])[0]
        if frame is None:return {'frames':frames,'frame_fields':p['frame_fields'],'points':[],'note':p.get('note')}
        if frame not in frames:fail('坐标组未登记',400)
        import math
        points=[]
        for i,r in enumerate(rows):
            f=r['fields']
            if '|'.join(str(f.get(k)) for k in p['frame_fields'])!=frame:continue
            x,y=f.get(p['x']),f.get(p['y'])
            if type(x) not in (int,float) or type(y) not in (int,float) or not math.isfinite(x) or not math.isfinite(y):continue
            points.append({'ordinal':i,'native_id':r['id'],'x':x,'y':y})
        return {'frames':frames,'frame':frame,'frame_fields':p['frame_fields'],'points':points[:3000],'truncated':len(points)>3000,'note':p.get('note'),'source_id':t['source_id']}

def service(repository):
    with repository.lock:
        if not hasattr(repository,'game_study'):repository.game_study=GameStudy(repository)
        return repository.game_study
