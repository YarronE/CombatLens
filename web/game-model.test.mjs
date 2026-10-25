import test from 'node:test';import assert from 'node:assert/strict';
import {draft,validateDraft,addItem,compareDrafts,buildReport,recordKey,RequestGate,readingTarget,studyNavigation,studyHash} from './game-model.js';
test('drafts stay bound to source fingerprint and bounded native identities',()=>{const d=draft('one');assert.equal(validateDraft(d,'one').items.length,0);assert.throws(()=>validateDraft(d,'two'));for(const i of [{table:'../path',ordinal:0},{table:'items',ordinal:-1},{table:'items',ordinal:.5}])assert.throws(()=>validateDraft({...d,items:[i]},'one'));assert.throws(()=>validateDraft({...d,items:Array.from({length:25},(_,i)=>({table:'items',ordinal:i}))},'one'));});
test('foreign or duplicate physical rows cannot silently replace selected records',()=>{const d=addItem(draft('one'),{table:'items',ordinal:0});assert.equal(addItem(d,{table:'items',ordinal:0}).items.length,1);assert.equal(addItem(d,{table:'items',ordinal:1}).items.length,2);assert.throws(()=>validateDraft({...d,items:[...d.items,...d.items]},'one'));});
test('comparison reports literal membership and changed conditions',()=>{const a=addItem(draft('one'),{table:'items',ordinal:0}),b={...addItem(draft('one'),{table:'items',ordinal:1}),party:1};const c=compareDrafts(a,b);assert.equal(c.added[0].ordinal,1);assert.equal(c.removed[0].ordinal,0);assert.equal(c.conditions,true);});
test('mode restrictions and native color capacities use configured fields',()=>{const records=new Map(),c={table:'containers',ordinal:0,build_kind:'container',fields:{slot:0}},r={table:'items',ordinal:0,build_kind:'item',fields:{color:1,partition:0,restricted:true}};for(const v of [c,r])records.set(recordKey(v),v);const d={...draft('one'),items:[c,r]},config={mode_rules:[{kind:'item',field:'restricted',equals:true,requires_mode:'alternate',label:'Restricted item'}],slots:{item_kind:'item',container_kind:'container',color_field:'color',partition_field:'partition',partitions:{0:['slot']}}};const report=buildReport(d,records,config);assert.equal(report.gaps.length,2);r.fields.color=0;d.mode='alternate';assert.equal(buildReport(d,records,config).gaps.length,0);});
test('candidate pools and repeated references never become summed effect power',()=>{const r={table:'items',ordinal:0,fields:{value:0},references:[{table:'effects',native_id:10,status:'pool',mode:'pool',count:5}]},d=addItem(draft('one'),r),result=buildReport(d,new Map([[recordKey(r),r]]));assert.ok(result.info.some(t=>t.includes('候选池')));assert.equal(result.damage,undefined);assert.equal(result.probability,undefined);});
test('missing evidence is visible in the build report',()=>{const d=addItem(draft('one'),{table:'items',ordinal:1});assert.equal(buildReport(d,new Map()).ready,0);assert.ok(buildReport(d,new Map()).gaps.length>0);});
test('late searches and failures cannot overwrite a new system',async()=>{const gate=new RequestGate(),seen=[];let finish;const first=gate.run(()=>new Promise(r=>finish=r),r=>seen.push(r));await gate.run(async()=>2,r=>seen.push(r));finish(1);await first;assert.deepEqual(seen,[2]);gate.cancel();await gate.run(async()=>{throw new Error('gap')},()=>{},e=>seen.push(e.message));assert.equal(seen.at(-1),'gap');});

test('reading drilldown carries fact identity rather than dropping or stringifying predicates',()=>{
 const f={id:'bounded',scope:{where:{enabled:false},has_native_id:true,native_id:null}};
 const target=readingTarget(f,{id:'items',system_id:'prepare'});
 assert.equal(target.fact,'bounded');assert.equal(target.native,null);assert.equal(target.focus,'bounded');assert.equal(target.ordinal,null);
 const record=readingTarget({id:'row',ordinal:0},{id:'items',system_id:'prepare'});assert.equal(record.fact,null);assert.equal(record.ordinal,0);
});
test('scope persists through paging and search but clears across tables and systems',()=>{
 const s={view:'browse',system:'prepare',table:'items',chapter:'choice',fact:'bounded',focus:'bounded',offset:0,ordinal:3,q:''};
 for(const changes of [{offset:30},{q:'value 2'}]){const n=studyNavigation(s,changes);assert.equal(n.fact,'bounded');assert.equal(n.ordinal,null);}
 for(const changes of [{table:'effects'},{system:'growth',table:null},{view:'overview'}]){const n=studyNavigation(s,changes);assert.equal(n.fact,null);assert.equal(n.ordinal,null);}
 const n=studyNavigation(s,{view:'reading',focus:s.fact});assert.equal(n.focus,'bounded');assert.equal(n.chapter,'choice');assert.equal(n.fact,null);
 assert.equal(studyNavigation(n,{chapter:'other'}).focus,null);
});
test('hash retains exact measure identity, page and zero ordinal for refresh and history',()=>{
 const state={view:'browse',system:'prepare',table:'items',chapter:'choice',fact:'count & value',focus:'count & value',offset:30,ordinal:0,native:null,q:'flag=false'};
 const hash=studyHash(state),p=new URLSearchParams(hash.slice(1));
 for(const key of ['fact','focus','chapter','table','q'])assert.equal(p.get(key),state[key]);
 assert.equal(p.get('offset'),'30');assert.equal(p.get('ordinal'),'0');assert.equal(p.has('native'),false);
});
