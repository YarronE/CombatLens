// Mutable analysis deltas only; original research and server metadata never enter history.
import {clone} from './model.js';
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function sequenceOf(analysis,where){const sequence=analysis.objects.find(o=>o.id===where.objectId)?.sequences.find(s=>s.id===where.sequenceId);if(!sequence)throw new Error('找不到历史操作对应的序列。');return sequence}
function capture(analysis,where){const sequence=sequenceOf(analysis,where),original=sequence.events.find(e=>e.id===where.id);if(original)return {kind:'override',value:clone(original.analysis_override??null)};const index=(sequence.analysis_events||[]).findIndex(e=>e.id===where.id);return {kind:'addition',index:index<0?null:index,value:index<0?null:clone(sequence.analysis_events[index])}}
function restore(analysis,where,snapshot){const sequence=sequenceOf(analysis,where);if(snapshot.kind==='override'){const event=sequence.events.find(e=>e.id===where.id);if(!event)throw new Error('历史原始事件已不在副本中。');event.analysis_override=clone(snapshot.value)}else{sequence.analysis_events??=[];const index=sequence.analysis_events.findIndex(e=>e.id===where.id);if(index>=0)sequence.analysis_events.splice(index,1);if(snapshot.value!==null)sequence.analysis_events.splice(Math.min(snapshot.index,sequence.analysis_events.length),0,clone(snapshot.value))}}
export class EditHistory {
 constructor(limit=100){this.limit=limit;this.reset(null)}
 reset(id,dirty=false){this.id=id;this.undoStack=[];this.redoStack=[];this.serial=0;this.token=0;this.savedToken=dirty?null:0}
 get canUndo(){return this.undoStack.length>0} get canRedo(){return this.redoStack.length>0} get dirty(){return this.token!==this.savedToken}
 ensure(analysis){if(!analysis||analysis.analysis_id!==this.id)throw new Error('历史操作属于另一份分析副本。')}
 execute(analysis,where,mutate,label='事件修改'){
  this.ensure(analysis);const before=capture(analysis,where);
  try{mutate()}catch(error){restore(analysis,where,before);throw error}
  const after=capture(analysis,where);if(equal(before,after))return false;
  const command={where:clone(where),before,after,label,beforeToken:this.token,afterToken:++this.serial};
  this.undoStack.push(command);if(this.undoStack.length>this.limit)this.undoStack.shift();this.redoStack=[];this.token=command.afterToken;return true;
 }
 undo(analysis){this.ensure(analysis);const command=this.undoStack.at(-1);if(!command)return null;restore(analysis,command.where,command.before);this.undoStack.pop();this.redoStack.push(command);this.token=command.beforeToken;return command}
 redo(analysis){this.ensure(analysis);const command=this.redoStack.at(-1);if(!command)return null;restore(analysis,command.where,command.after);this.redoStack.pop();this.undoStack.push(command);this.token=command.afterToken;return command}
 markSaved(analysis){this.ensure(analysis);this.savedToken=this.token}
}
