import {finite} from './model.js';
export function timingStep(unit,choice='fine'){if(choice==='free')return 0;return unit==='frames'?(choice==='coarse'?5:1):(choice==='coarse'?0.1:0.01)}
export function adjustedTiming(event,delta,edge,{low,high,step=0}){
 if(!finite(event.start)||!finite(delta)||!finite(low)||!finite(high)||high<=low||!finite(step)||step<0||!['move','start','end'].includes(edge))throw new Error('时间拖拽坐标不合法。');
 const interval=finite(event.end)&&event.end>event.start;
 if(edge!=='move'&&!interval)throw new Error('时间点事件没有区间端点。');
 let change=step>0?Math.round(delta/step)*step:delta;
 const result={start:event.start,end:event.end??null};
 if(edge==='move'){const last=finite(event.end)?event.end:event.start;change=Math.max(low-event.start,Math.min(high-last,change));result.start+=change;if(finite(event.end))result.end+=change}
 else{const minimum=Math.min(event.end-event.start,step||1e-6);if(edge==='start')result.start=Math.max(low,Math.min(event.end-minimum,event.start+change));else result.end=Math.min(high,Math.max(event.start+minimum,event.end+change))}
 result.start=Number(result.start.toFixed(9));if(finite(result.end))result.end=Number(result.end.toFixed(9));return result;
}

// Shared lifecycle; injectable EventTargets allow deterministic cancel-path checks.
export function capturePointerGesture(target,pointerId,{onMove,onEnd,onError=()=>{}},windowTarget=window){
 let finished=false;
 const move=e=>{if(e.pointerId!==pointerId||finished)return;e.preventDefault();try{onMove(e)}catch(error){onError(error);end(false)}};
 const up=e=>{if(e.pointerId!==pointerId||finished)return;move(e);if(!finished)end(true)};
 const cancel=e=>{if(e.pointerId===undefined||e.pointerId===pointerId)end(false)};
 const key=e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();end(false)}};
 function end(commit){if(finished)return;finished=true;target.removeEventListener('pointermove',move);target.removeEventListener('pointerup',up);target.removeEventListener('pointercancel',cancel);target.removeEventListener('lostpointercapture',cancel);windowTarget.removeEventListener('blur',cancel);windowTarget.removeEventListener('keydown',key,true);if(target.hasPointerCapture(pointerId))target.releasePointerCapture(pointerId);onEnd(commit)}
 target.addEventListener('pointermove',move);target.addEventListener('pointerup',up);target.addEventListener('pointercancel',cancel);target.addEventListener('lostpointercapture',cancel);windowTarget.addEventListener('blur',cancel);windowTarget.addEventListener('keydown',key,true);target.setPointerCapture(pointerId);
 return {cancel:()=>end(false)};
}

export function timelineLanes(events){
 const tracks=[];let offset=0;
 for(const key of [...new Set(events.map(e=>e.track||'事件'))]){
  const ends=[],lanes=new Map();
  for(const event of events.filter(e=>(e.track||'事件')===key).sort((a,b)=>a.start-b.start||String(a.id).localeCompare(String(b.id)))){
   let lane=ends.findIndex(end=>end<=event.start);if(lane<0)lane=ends.length;
   ends[lane]=finite(event.end)&&event.end>event.start?event.end:event.start+1e-9;lanes.set(event.id,lane);
  }
  tracks.push({key,offset,count:ends.length,lanes});offset+=ends.length;
 }
 return {tracks,rows:offset};
}
