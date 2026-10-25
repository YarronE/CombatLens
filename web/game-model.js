export const MAX_DRAFT_ITEMS=24;
export const recordKey=r=>r.table+':'+r.ordinal;
export function draft(fp,name='Build A'){return {schema:'combatlens-build/1',package_fingerprint:fp,name,mode:'standard',party:3,notes:'',items:[]};}
export function validateDraft(value,fp){
 if(!value||value.schema!=='combatlens-build/1'||value.package_fingerprint!==fp)throw new Error('草稿来源版本不符，请在原研究包中打开。');
 if(typeof value.name!=='string'||value.name.length>120||typeof value.notes!=='string'||value.notes.length>4000||typeof value.mode!=='string'||!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(value.mode)||![1,2,3].includes(value.party)||!Array.isArray(value.items)||value.items.length>MAX_DRAFT_ITEMS)throw new Error('Build 草稿格式或范围无效。');
 const seen=new Set();for(const item of value.items){if(!item||typeof item.table!=='string'||!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(item.table)||!Number.isSafeInteger(item.ordinal)||item.ordinal<0||item.ordinal>200000||seen.has(recordKey(item)))throw new Error('草稿物理行无效或重复。');seen.add(recordKey(item));}
 return {schema:value.schema,package_fingerprint:fp,name:value.name,mode:value.mode,party:value.party,notes:value.notes,items:value.items.map(i=>({table:i.table,ordinal:i.ordinal}))};
}
export function addItem(value,record){const item={table:record.table,ordinal:record.ordinal};if(value.items.some(i=>recordKey(i)===recordKey(item)))return value;if(value.items.length>=MAX_DRAFT_ITEMS)throw new Error('研究草稿最多保留 24 项。');return {...value,items:[...value.items,item]};}
export function compareDrafts(a,b){const ak=new Set(a.items.map(recordKey)),bk=new Set(b.items.map(recordKey));return {added:b.items.filter(i=>!ak.has(recordKey(i))),removed:a.items.filter(i=>!bk.has(recordKey(i))),conditions:a.mode!==b.mode||a.party!==b.party};}
export function buildReport(value,records,config={}){
 const ready=value.items.map(i=>records.get(recordKey(i))).filter(Boolean),gaps=[],info=[];
 if(ready.length<value.items.length)gaps.push('部分记录未完成当前来源核验。');
 for(const limit of config.role_limits||[]){if(ready.filter(r=>r.build_kind===limit.kind).length>limit.max)gaps.push(limit.label+'超过草稿配置的数量。');}
 for(const rule of config.mode_rules||[]){if(value.mode!==rule.requires_mode&&ready.some(r=>r.build_kind===rule.kind&&r.fields?.[rule.field]===rule.equals))gaps.push(rule.label+'要求 '+(rule.mode_label||rule.requires_mode)+'。');}
 const slots=config.slots,container=slots&&ready.find(r=>r.build_kind===slots.container_kind);
 if(slots&&!container&&ready.some(r=>r.build_kind===slots.item_kind))gaps.push('未选择容器，槽位颜色和数量尚未核对。');
 if(container){for(const [partition,slotFields]of Object.entries(slots.partitions||{})){const capacity=new Map();for(const field of slotFields){const color=container.fields?.[field];if(color!==null&&color!==undefined)capacity.set(color,(capacity.get(color)||0)+1);}for(const item of ready.filter(r=>r.build_kind===slots.item_kind&&String(r.fields?.[slots.partition_field])===partition)){const color=item.fields?.[slots.color_field],n=capacity.get(color)||0;if(n<=0)gaps.push('槽位原始颜色码 '+color+' 的数量不足。');else capacity.set(color,n-1);}}}
 const pools=ready.flatMap(r=>(r.references||[]).filter(ref=>ref.mode==='pool')),unresolved=ready.flatMap(r=>(r.references||[]).filter(ref=>['missing','ambiguous','gap'].includes(ref.status)));
 if(pools.length)info.push(pools.length+' 条候选池引用，未按同时生效效果计算。');if(unresolved.length)gaps.push(unresolved.length+' 条引用缺失、歧义或失效。');
 const ids=new Map();for(const r of ready)for(const ref of r.references||[]){if(ref.status==='exact'&&(config.trace_tables||[]).includes(ref.table)){const key=ref.table+':'+ref.native_id;ids.set(key,(ids.get(key)||0)+1);}}
 for(const [id,count]of ids)if(count>1)info.push(id+' 被 '+count+' 个已选字段引用，叠加规则待确认。');
 info.push('字段检查未覆盖全部解锁和角色适用规则。');info.push('检查配置字段与引用；未计算最终伤害、掉落概率或最优配装。');return {gaps:[...new Set(gaps)],info,ready:ready.length};
}
export class RequestGate{constructor(){this.id=0;}cancel(){this.id++;}async run(fetcher,apply,fail=()=>{}){const token=++this.id;try{const data=await fetcher();if(token===this.id)apply(data);}catch(e){if(token===this.id)fail(e);}}}

// A measure identity is resolved against registered evidence by the server.
export function readingTarget(fact,table){
 return {view:'browse',system:table.system_id,table:table.id,q:'',native:null,
  fact:fact.scope?fact.id:null,focus:fact.id,offset:0,ordinal:fact.ordinal??null};
}
export function studyNavigation(state,changes){
 const changed=key=>Object.hasOwn(changes,key)&&changes[key]!==state[key];
 const next={...state,...changes};
 if(!Object.hasOwn(changes,'fact')&&(changed('table')||changed('system')||next.view!=='browse'))next.fact=null;
 if(!Object.hasOwn(changes,'focus')&&changed('chapter'))next.focus=null;
 if(!Object.hasOwn(changes,'ordinal')&&['view','system','table','q','native','fact','offset'].some(changed))next.ordinal=null;
 return next;
}
export function studyHash(state){
 const p=new URLSearchParams({view:state.view,system:state.system});
 for(const key of ['chapter','table','q','native','offset','ordinal','fact','focus']){
  const v=state[key];if(v!==null&&v!==undefined&&v!=='')p.set(key,v);
 }
 return '#'+p;
}
