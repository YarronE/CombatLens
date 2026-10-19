export const UNITS = new Set(['seconds','frames','game_seconds','source_units']);
export const clone = value => structuredClone(value);
export const finite = value => typeof value === 'number' && Number.isFinite(value);
export const unitLabel = unit => ({seconds:'秒',frames:'帧',game_seconds:'游戏秒',source_units:'来源单位'}[unit] || '单位未知');
export const valueText = value => value === null || value === undefined ? '未知' : typeof value === 'object' ? JSON.stringify(value,null,2) : String(value);
export function freezeDeep(value) { if(value && typeof value === 'object' && !Object.isFrozen(value)) { Object.freeze(value); Object.values(value).forEach(freezeDeep); } return value; }
export function effectiveEvent(event, sequence, analysisMode) {
  const override = analysisMode && event.analysis_override;
  const addition = analysisMode && event.kind === 'analysis_event';
  return { ...event, start:override ? override.start : event.start, end:override ? override.end : event.end,
    unit:override ? override.unit : addition ? event.unit : sequence.unit,
    hypothesis:Boolean(override || addition), note:override?.note ?? (addition ? event.note : ''), reason:override?.reason ?? (addition ? event.reason : '') };
}
export function isTimed(event, sequence) {
  if(!finite(event.start) || !UNITS.has(event.unit)) return false;
  if(event.end !== null && event.end !== undefined && !finite(event.end)) return false;
  if(finite(event.end) && event.end < event.start) return false;
  if(event.hypothesis) return true;
  return event.timing_status !== 'unknown' && Boolean(sequence.origin?.kind) && sequence.origin.kind !== 'unknown';
}
function fields(value, required, optional, message) {
  if(!value || typeof value !== 'object' || Array.isArray(value) || required.some(k=>!Object.hasOwn(value,k)) || Object.keys(value).some(k=>!required.includes(k)&&!optional.includes(k))) throw new Error(message);
}
export function finiteJSON(value, depth=0) {
  if(depth>100) throw new Error('JSON 参数嵌套超过 100 层。');
  if(typeof value==='number'&&!finite(value)) throw new Error('JSON 参数包含非有限数值。');
  if(value&&typeof value==='object') Object.values(value).forEach(v=>finiteJSON(v,depth+1));
  else if(value!==null&&!['number','string','boolean'].includes(typeof value)) throw new Error('参数需要可保存的 JSON 值。');
}
export function validateOverride(value) {
  fields(value,['start','end','unit','note','reason','timing_status'],['parameters','deleted'],'分析修改含缺失或不受支持的字段。');
  for(const name of ['start','end']) if(value[name] !== null && !finite(value[name])) throw new Error(name === 'start' ? '开始时刻必须是有限数值或未知。' : '结束时刻必须是有限数值或未知。');
  if(value.start === null && value.end !== null) throw new Error('填写结束时刻前需要填写开始时刻。');
  if(value.start !== null && value.end !== null && value.end < value.start) throw new Error('结束时刻不能早于开始时刻。');
  if(value.unit !== null && !UNITS.has(value.unit)) throw new Error('单位不受支持。');
  if(value.start !== null && value.unit === null) throw new Error('为分析时刻选择单位；没有时间依据时可以保留未知。');
  if(value.timing_status!=='analyst_hypothesis') throw new Error('分析修改必须保持人工假设状态。');
  if(typeof value.reason !== 'string' || !value.reason.trim() || value.reason.length>10000) throw new Error('填写修改理由后应用或保存，最多 10000 字。');
  if(typeof value.note !== 'string'||value.note.length>10000) throw new Error('分析备注需要是文本，最多 10000 字。');
  if(Object.hasOwn(value,'parameters')) finiteJSON(value.parameters);
  if(Object.hasOwn(value,'deleted')&&typeof value.deleted!=='boolean') throw new Error('删除标记需要是布尔值。');
  return value;
}
function validateAddition(event) {
  fields(event,['id','label','kind','track','start','end','unit','note','reason','parameters','timing_status'],['source_ids'],'新增分析事件含缺失或不受支持的字段。');
  if(!/^analysis-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(event.id)||event.kind!=='analysis_event') throw new Error('新增事件需要 analysis-UUID ID 与分析事件类型。');
  for(const key of ['label','track']) if(typeof event[key]!=='string'||!event[key].trim()||event[key].length>200) throw new Error('新增事件名称与轨道需要非空文本，最多 200 字。');
  if(event.source_ids!==undefined&&(!Array.isArray(event.source_ids)||event.source_ids.some(id=>typeof id!=='string'))) throw new Error('来源引用需要字符串数组。');
  validateOverride(Object.fromEntries(['start','end','unit','note','reason','parameters','timing_status'].map(k=>[k,event[k]])));
}
function strippedObjects(objects,validate=false) {
  const result=clone(objects),ids=new Set();
  if(!Array.isArray(result)) throw new Error('分析对象需要列表。');
  for(const object of result) {
    if(!Array.isArray(object?.sequences)) throw new Error('分析序列结构不合法。');
    for(const sequence of object.sequences) {
      const additions=sequence.analysis_events??[];
      if(!Array.isArray(additions)||!Array.isArray(sequence.events)) throw new Error('分析事件结构不合法。');
      if(validate) for(const event of additions) {validateAddition(event);if(ids.has(event.id))throw new Error('分析事件 ID 重复。');ids.add(event.id);}
      delete sequence.analysis_events;
      for(const event of sequence.events) {if(typeof event.id!=='string'||ids.has(event.id))throw new Error('事件 ID 重复或不合法。');ids.add(event.id);if(validate&&event.analysis_override!==null&&event.analysis_override!==undefined)validateOverride(event.analysis_override);event.analysis_override=null;}
    }
  }
  return result;
}
function canonical(value) { if(Array.isArray(value)) return '['+value.map(canonical).join(',')+']'; if(value&&typeof value==='object') return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}'; return JSON.stringify(value); }
export function validateAnalysis(value, source, strictFingerprint = false) {
  fields(value,['schema_version','analysis_id','name','revision','game_build','parent_package_fingerprint','objects'],['saved_at','validity'],'分析 JSON 含缺失或不受支持的顶层字段。');
  if(value.schema_version !== 'timeline-analysis/1') throw new Error('仅支持 timeline-analysis/1 的分析 JSON。');
  if(value.game_build !== source.game_build && strictFingerprint) throw new Error('该分析副本属于不同的游戏 Build，当前内容已保留。');
  if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(value.analysis_id || '')) throw new Error('分析 ID 不合法。');
  if(typeof value.name !== 'string' || !value.name.trim()||value.name.length>200) throw new Error('分析副本需要名称，最多 200 字。');
  if(!Number.isSafeInteger(value.revision) || value.revision < 0) throw new Error('分析修订号不合法。');
  if(strictFingerprint && value.parent_package_fingerprint !== source.package_fingerprint) throw new Error('导入副本的来源版本不匹配，当前分析已保留。');
  finiteJSON(value);
  const stripped=strippedObjects(value.objects,true);
  if(strictFingerprint && canonical(stripped)!==canonical(strippedObjects(source.objects))) throw new Error('原始对象、图、事件与来源值只读；导入内容修改了原始证据。');
  return value;
}
