import {finite,isTimed,effectiveEvent} from './model.js';
const CONFIRMED=new Set(['authored_montage_seconds','authored_frames','source_frame_only','native_seconds','confirmed','synthetic']);
export function studyEvents(sequence,affected=[]){
 const stale=new Set(affected),known=[],unknown=[];
 for(const original of sequence?.events||[]){const event=effectiveEvent(original,sequence,false);const valid=original.unit===sequence.unit&&!stale.has(event.id)&&CONFIRMED.has(event.timing_status)&&isTimed(event,sequence);(valid?known:unknown).push(event);}
 known.sort((a,b)=>a.start-b.start);return {known,unknown};
}
export function studyContext(data,source,object,sequence){
 if(data?.status!=='ready'||data.game_build!==source.game_build||data.package_fingerprint!==source.package_fingerprint)return null;
 return data.entries.find(e=>e.object_id===object?.id&&e.sequence_id===sequence?.id)||null;
}
export function intervals(events){return events.slice(1).map((event,i)=>({from:events[i].id,to:event.id,value:event.start-events[i].start,unit:event.unit})).filter(x=>finite(x.value)&&x.value>=0);}
export class StudyRequestGate{constructor(){this.epoch=0;this.key=null;}async load(key,fetcher,apply){const token=++this.epoch;this.key=key;try{const result=await fetcher();if(token===this.epoch&&this.key===key)apply(result);}catch{if(token===this.epoch&&this.key===key)apply({status:'unavailable',entries:[]});}}cancel(){this.epoch++;this.key=null;}}
