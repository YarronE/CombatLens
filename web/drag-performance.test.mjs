import test from 'node:test';
import assert from 'node:assert/strict';
import {capturePointerGesture,bindTimelineScrub} from './timeline-edit.js';
import {AssetViewer} from './viewer.js';
import {PlaybackClock} from './preview-model.js';
import {EditHistory} from './edit-history.js';
class Target extends EventTarget{setPointerCapture(id){this.pointer=id;}hasPointerCapture(id){return this.pointer===id;}releasePointerCapture(){this.pointer=null;}}
function scheduler(){let id=0;const pending=new Map();return {requestFrame:fn=>{pending.set(++id,fn);return id;},cancelFrame:key=>pending.delete(key),step(){const work=[...pending.values()];pending.clear();work.forEach(fn=>fn());},get pending(){return pending.size;}};}
function send(target,type,x=0,extra={}){const e=new Event(type,{cancelable:true});Object.assign(e,{pointerId:1,button:0,clientX:x,clientY:0,...extra});target.dispatchEvent(e);return e;}
test('pointer bursts paint only the latest sample and pointerup flushes exact final input',()=>{
 const target=new Target(),win=new EventTarget(),frames=scheduler(),seen=[],ended=[];
 capturePointerGesture(target,1,{coalesce:true,...frames,onMove:e=>seen.push(e.clientX),onEnd:v=>ended.push(v)},win);
 for(let i=1;i<=1000;i++)send(target,'pointermove',i);
 assert.equal(frames.pending,1);assert.deepEqual(seen,[]);frames.step();assert.deepEqual(seen,[1000]);
 send(target,'pointermove',1001);send(target,'pointerup',1002);assert.deepEqual(seen,[1000,1002]);assert.deepEqual(ended,[true]);assert.equal(frames.pending,0);frames.step();assert.deepEqual(seen,[1000,1002]);
});
test('coalesced event drag commits once and undo restores the source-backed copy',()=>{
 const target=new Target(),win=new EventTarget(),frames=scheduler(),history=new EditHistory();
 const copy={analysis_id:'synthetic-copy',revision:0,objects:[{id:'actor',sequences:[{id:'sequence',events:[{id:'event',start:1,end:2,raw_value:{original:7},analysis_override:null}]}]}]};
 const event=copy.objects[0].sequences[0].events[0],where={objectId:'actor',sequenceId:'sequence',id:'event'};history.reset(copy.analysis_id);
 let proposed=1,commits=0;
 capturePointerGesture(target,1,{coalesce:true,...frames,onMove:e=>proposed=e.clientX,onEnd:commit=>{if(commit){commits++;history.execute(copy,where,()=>event.analysis_override={start:proposed,end:proposed+1},'drag');}}},win);
 for(let i=0;i<200;i++)send(target,'pointermove',i/100);send(target,'pointerup',3.25);
 assert.equal(commits,1);assert.equal(event.analysis_override.start,3.25);assert.equal(event.start,1);assert.deepEqual(event.raw_value,{original:7});history.undo(copy);assert.equal(event.analysis_override,null);history.redo(copy);assert.equal(event.analysis_override.start,3.25);
});
test('cancel paths discard pending samples and never commit a queued drag',()=>{
 for(const cancel of ['pointercancel','lostpointercapture','Escape','blur']){
  const target=new Target(),win=new EventTarget(),frames=scheduler(),seen=[],ended=[];
  capturePointerGesture(target,1,{coalesce:true,...frames,onMove:e=>seen.push(e.clientX),onEnd:v=>ended.push(v)},win);
  send(target,'pointermove',9);
  if(cancel==='Escape')send(win,'keydown',0,{key:'Escape'});else if(cancel==='blur')win.dispatchEvent(new Event('blur'));else send(target,cancel);
  frames.step();send(target,'pointerup',10);assert.deepEqual(seen,[]);assert.deepEqual(ended,[false]);assert.equal(frames.pending,0);
 }
});
test('continuous scrub retains the starting position on cancellation and rejects stale context',()=>{
 const target=new Target(),win=new EventTarget(),frames=scheduler(),seen=[];let time=.25,previous,active=true,ended=[];
 bindTimelineScrub(target,{...frames,windowTarget:win,canStart:()=>active,position:e=>e.clientX,isCurrent:()=>active,onStart:()=>previous=time,seek:t=>{time=t;seen.push(t);},onFinish:commit=>{ended.push(commit);if(!commit&&active)time=previous;}});
 send(target,'pointerdown',.5);send(target,'pointermove',1.2);frames.step();assert.equal(time,1.2);
 send(win,'keydown',0,{key:'Escape'});assert.equal(time,.25);assert.deepEqual(ended,[false]);
 send(target,'pointerdown',.8);send(target,'pointermove',1.4);active=false;frames.step();assert.equal(time,.8);assert.deepEqual(ended,[false,false]);assert.equal(frames.pending,0);
});
test('scrub errors roll back once without leaking a pending frame',()=>{
 const target=new Target(),win=new EventTarget(),frames=scheduler(),ended=[],errors=[];
 capturePointerGesture(target,1,{coalesce:true,...frames,onMove:()=>{throw Error('synthetic failure');},onError:e=>errors.push(e.message),onEnd:v=>ended.push(v)},win);
 send(target,'pointermove',1);frames.step();send(target,'pointerup',2);assert.deepEqual(errors,['synthetic failure']);assert.deepEqual(ended,[false]);assert.equal(frames.pending,0);
});
test('loaded viewer seeks preserve playback range and skip repeated pose sampling',()=>{
 const viewer=Object.create(AssetViewer.prototype),samples=[];
 viewer.clip={clip_duration_seconds:1,clock_mapping:{status:'proven',unit:'frames',action_in:0,action_out:24,clip_in:0,clip_out:1,play_rate:1,seconds_per_unit:1/24,source_ids:['synthetic']}};
 viewer.clock=new PlaybackClock(t=>samples.push(t));viewer.clock.configure(1);viewer.clock.setRange(.1,.8);samples.length=0;viewer.updateControls=()=>{};
 viewer.clock.playing=true;assert.equal(viewer.seekAction(12,'frames'),true);assert.equal(viewer.clock.playing,false);assert.equal(viewer.clock.time,.5);assert.deepEqual(samples,[.5]);
 viewer.seekAction(12,'frames');assert.deepEqual(samples,[.5]);assert.deepEqual(viewer.clock.range,{start:.1,end:.8});
});
