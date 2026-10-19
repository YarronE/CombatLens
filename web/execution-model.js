const shaPattern=/^[a-f0-9]{64}$/i;
export function executionSourceCandidates(sources){
  return (sources||[]).filter(source=>['path','snapshot_path','original_path'].some(key=>typeof source[key]==='string'&&source[key].replaceAll('\\','/').split('/').at(-1)==='notify-execution-summary.json'));
}
export function parseExecutionSource(source,envelope,gameBuild){
  if(envelope?.source_id!==source?.id)throw new Error('执行摘要来源 ID 与登记不一致。');
  if(envelope.validity?.status!=='current')throw new Error('执行摘要来源状态为 '+(envelope.validity?.status||'unknown')+'，执行依据待重新核对。');
  const expected=source.sha256,actual=envelope.validity?.sha256,registered=envelope.validity?.expected_sha256;
  if(!shaPattern.test(expected||'')||!shaPattern.test(actual||'')||expected.toLowerCase()!==actual.toLowerCase()||(registered!==undefined&&registered!==null&&registered.toLowerCase()!==expected.toLowerCase()))throw new Error('执行摘要 SHA256 与本页登记不一致，请重新读取当前研究包。');
  let content=envelope.content;
  if(typeof content==='string'){try{content=JSON.parse(content);}catch{throw new Error('执行摘要文本不能解析为 JSON。');}}
  if(!content||content.schema_version!=='notify-execution-summary/1'||content.game_build!==gameBuild||!Array.isArray(content.rules))throw new Error('执行摘要 schema 或 Build 与当前研究包不一致。');
  const ids=new Set();for(const rule of content.rules){if(!rule||typeof rule.id!=='string'||!rule.id||ids.has(rule.id))throw new Error('执行摘要规则 ID 缺失或重复。');ids.add(rule.id);}
  return content;
}
export function filterExecutionRules(summary,event,sequence){
  const notify=[],skill=[],gaps=[],ids=new Set(Array.isArray(event?.execution_rule_ids)?event.execution_rule_ids:[]),raw=event?.raw_value||{},buff=raw.notify_object_properties?.BuffID?.value,action=sequence?.action_id,known=new Set();
  for(const rule of summary.rules){
    known.add(rule.id);const isStage=rule.category==='resource_stage'&&rule.class_path===undefined&&rule.class_paths===undefined;
    const actionMatches=rule.action_id===undefined||Number.isSafeInteger(rule.action_id)&&Number.isSafeInteger(action)&&rule.action_id===action;
    if(isStage){if(rule.action_id!==undefined&&actionMatches)skill.push(rule);else if(ids.has(rule.id))gaps.push({id:rule.id,reason:'技能阶段规则的 action_id 与当前招式不匹配。'});continue;}
    if(!ids.has(rule.id))continue;
    if(!actionMatches){gaps.push({id:rule.id,reason:'规则 action_id 与当前招式不匹配。'});continue;}
    if(rule.buff_id!==undefined&&(!Number.isSafeInteger(rule.buff_id)||!Number.isSafeInteger(buff)||rule.buff_id!==buff)){gaps.push({id:rule.id,reason:'原始 BuffID '+String(buff??'未知')+' 与规则 BuffID '+String(rule.buff_id)+' 不匹配。'});continue;}
    if(rule.required_values){let valid=true;for(const [path,value] of Object.entries(rule.required_values)){let current=raw;for(const part of path.split('.'))current=current?.[part];if(current!==value)valid=false}if(!valid){gaps.push({id:rule.id,reason:'原始实例字段不满足规则条件。'});continue;}}
    const paths=Array.isArray(rule.class_paths)?rule.class_paths:typeof rule.class_path==='string'?[rule.class_path]:[];
    if(!paths.length||!paths.every(path=>typeof path==='string')||!paths.includes(raw.class_path)){gaps.push({id:rule.id,reason:'原始 Notify class_path 与规则执行类缺少可靠匹配。'});continue;}
    notify.push(rule);
  }
  for(const id of ids)if(!known.has(id))gaps.push({id,reason:'当前摘要尚未提供该执行规则。'});
  return {notify,skill,gaps};
}
