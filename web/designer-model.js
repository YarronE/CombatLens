import {filterExecutionRules} from './execution-model.js';
const statuses=new Set(['static_cil_verified','asset_data_cil_join_verified']);
export function originalValue(root,path){if(typeof path!=='string'||!/^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*$/.test(path))return undefined;let value=root;for(const part of path.split('.')){if(['__proto__','prototype','constructor'].includes(part)||!value||!Object.hasOwn(value,part))return undefined;value=value[part];}return value;}
function scalar(value){return typeof value==='string'||typeof value==='boolean'||typeof value==='number'&&Number.isFinite(value);}
export function designerDetails(summary,guide,event,sequence,context={}){
 const unknown=reason=>({status:'unknown',reason,notify:[],skill:[],gaps:[]});
 if(context.stale)return unknown('来源已变化，作用未确认');
 if(guide?.status!=='ready')return unknown(guide?.status==='unavailable'?'解释证据未通过核验':'作用未确认');
 if(guide.schema!=='combatlens-event-guide/1'||!Array.isArray(guide.dependencies)||!guide.dependencies.length||!/^[a-f0-9]{64}$/i.test(guide.guide_sha256||'')||guide.game_build!==context.gameBuild||guide.package_fingerprint!==context.fingerprint||guide.execution_source?.id!==context.source?.id||guide.execution_source?.sha256!==context.source?.sha256||!Array.isArray(guide.entries)||!Array.isArray(guide.affected_event_ids)||guide.affected_event_ids.includes(event.id))return unknown('解释与当前事件来源不一致');
 const seen=new Set();for(const note of guide.entries){if(!note||typeof note.rule_id!=='string'||seen.has(note.rule_id)||!['title','effect','boundary'].every(k=>typeof note[k]==='string'&&note[k].trim())||!Array.isArray(note.conditions)||!note.conditions.length||!note.conditions.every(c=>typeof c==='string')||!Array.isArray(note.numbers)||!note.numbers.every(n=>n&&['rule','event'].includes(n.scope)&&typeof n.label==='string'&&typeof n.path==='string'&&typeof n.unit==='string')||note.required_values&&(typeof note.required_values!=='object'||Array.isArray(note.required_values)))return unknown('解释条目未确认');seen.add(note.rule_id);}
 const selected=filterExecutionRules(summary,event,sequence),gaps=[...selected.gaps];
 const join=rules=>rules.flatMap(rule=>{const note=guide.entries.find(n=>n.rule_id===rule.id);if(!note||!statuses.has(rule.execution_status))return [];
 if(note.action_id!==undefined&&(!Number.isSafeInteger(note.action_id)||note.action_id!==sequence.action_id)){gaps.push({id:rule.id,reason:'解释的招式限定不匹配'});return [];}
 if(note.required_values&&Object.entries(note.required_values).some(([path,value])=>originalValue(event.raw_value,path)!==value)){gaps.push({id:rule.id,reason:'原始实例参数不满足解释限定'});return [];}
 const numbers=note.numbers.map(item=>{const value=item.scope==='rule'?originalValue(rule,item.path):item.scope==='event'?originalValue(event.raw_value,item.path):undefined;return {label:item.label,value:scalar(value)?value:null,unit:typeof item.unit==='string'?item.unit:'未确认',note:item.note||'来源原值',scope:item.scope,path:item.path};});return [{...note,numbers,rule}];});
 const notify=join(selected.notify),skill=join(selected.skill);return {status:notify.length?'verified':'unknown',reason:notify.length?'静态证据':'本条Notify的作用、触发条件与数值尚未确认',notify,skill,gaps};
}
