import {finite} from './model.js';
export function clockMapping(clip, duration=clip?.clip_duration_seconds) {
  const m=clip?.clock_mapping;
  if(!m||m.status!=='proven'||!['seconds','frames'].includes(m.unit)||!Array.isArray(m.source_ids)||!m.source_ids.length)return null;
  if(!['action_in','action_out','clip_in','clip_out','play_rate'].every(k=>finite(m[k]))||m.play_rate<=0||m.action_in<0||m.clip_in<0||m.action_out<=m.action_in||m.clip_out<=m.clip_in)return null;
  const scale=m.unit==='seconds'?(m.seconds_per_unit??1):m.seconds_per_unit;if(!finite(scale)||scale<=0||m.unit==='seconds'&&scale!==1)return null;
  if(Math.abs((m.action_out-m.action_in)*m.play_rate*scale-(m.clip_out-m.clip_in))>1e-5)return null;
  if(finite(duration)&&m.clip_out>duration+1e-5)return null;
  return m;
}
export function actionToClip(time,unit,clip) {
  const m=clockMapping(clip);if(!m||unit!==m.unit||!finite(time)||time<m.action_in-1e-7||time>m.action_out+1e-7)return null;
  return Math.max(m.clip_in,Math.min(m.clip_out,m.clip_in+(time-m.action_in)*m.play_rate*(m.seconds_per_unit??1)));
}
export function clipToAction(time,clip) {
  const m=clockMapping(clip);if(!m||!finite(time)||time<m.clip_in-1e-7||time>m.clip_out+1e-7)return null;
  return m.action_in+(time-m.clip_in)/(m.play_rate*(m.seconds_per_unit??1));
}
export function sampleTimes(values,duration) {
  if(!Array.isArray(values))return [];
  const tolerance=Math.max(1e-6,Math.abs(duration)*2**-23);
  return [...new Set(values.filter(v=>finite(v)&&v>=0&&v<=duration+tolerance).map(v=>Math.min(v,duration)))].sort((a,b)=>a-b);
}
export class PlaybackClock {
  constructor(onChange=()=>{}) {this.onChange=onChange;this.duration=0;this.time=0;this.speed=1;this.sourceRate=1;this.playing=false;this.range={start:0,end:0};this.loop=false;}
  configure(duration,sourceRate=1) {if(!finite(duration)||duration<0)throw new Error('动画片段时长不合法。');if(!finite(sourceRate)||sourceRate<=0)throw new Error('已确认的原始播放速率不合法。');this.duration=duration;this.sourceRate=sourceRate;this.playing=false;this.range={start:0,end:duration};this.loop=false;this.seek(0);}
  setRange(start,end) {if(!finite(start)||!finite(end)||start<0||end>this.duration+1e-7||end<=start)throw new Error('播放区间需要在当前动画段内，且结束晚于开始。');const bounded=Math.min(end,this.duration);if(bounded<=start)throw new Error('播放区间没有长度。');this.pause();this.range={start,end:bounded};return this.range;}
  seek(time) {if(!finite(time))throw new Error('播放位置必须是有限数值。');this.time=Math.max(0,Math.min(this.duration,time));this.onChange(this.time);return this.time;}
  tick(delta) {if(!this.playing||!finite(delta)||delta<0)return;const {start,end}=this.range,length=end-start;if(length<=0){this.pause();return;}const next=(this.time<start||this.time>=end?start:this.time)+delta*this.sourceRate*this.speed;if(next>=end){if(this.loop)this.seek(start+((next-start)%length));else{this.playing=false;this.seek(end);}}else this.seek(next);}
  toggle() {const {start,end}=this.range;if(end<=start)return false;if(!this.playing&&(this.time<start||this.time>=end))this.seek(start);this.playing=!this.playing;return this.playing;}
  pause() {this.playing=false;}
  step(direction,keys) {this.pause();const times=sampleTimes(keys,this.duration),epsilon=1e-7;const candidate=direction>0?times.find(t=>t>this.time+epsilon):times.filter(t=>t<this.time-epsilon).at(-1);if(candidate===undefined)return false;this.seek(candidate);return true;}
}
export function inspectGLB(buffer,{kind='skinned_animation'}={}) {
  if(!['skinned_animation','static_mesh'].includes(kind))throw new Error('预览类型未支持。');
  if(!(buffer instanceof ArrayBuffer)||buffer.byteLength<20)throw new Error('GLB 文件头不完整。');
  const view=new DataView(buffer);
  if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(8,true)!==buffer.byteLength)throw new Error('GLB 文件头或总长度不合法。');
  const length=view.getUint32(12,true);if(view.getUint32(16,true)!==0x4e4f534a||length>8*1024*1024||length%4!==0||length>buffer.byteLength-28)throw new Error('GLB JSON chunk 不合法。');
  const json=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,length)).trim());
  if(json.asset?.version!=='2.0')throw new Error('仅支持 glTF 2.0。');
  if((json.buffers||[]).some(b=>b.uri!==undefined)||(json.images||[]).some(i=>i.uri!==undefined))throw new Error('仅支持自包含 GLB，资源 URI 不受允许。');
  if((json.extensionsRequired||[]).length)throw new Error('本版 GLB 不接入 required 扩展：'+json.extensionsRequired.join(', '));
  if(json.buffers?.length!==1)throw new Error('GLB 需要一个内嵌 buffer。');
  const binStart=20+length,binLength=view.getUint32(binStart,true),binType=view.getUint32(binStart+4,true),declared=json.buffers[0].byteLength;
  if(binType!==0x004e4942||binLength%4!==0||binStart+8+binLength!==buffer.byteLength||!Number.isSafeInteger(declared)||declared<0||binLength-declared<0||binLength-declared>3)throw new Error('GLB BIN 或 buffer 长度不匹配。');
  if(kind==='static_mesh'){if(json.skins?.length||json.animations?.length||json.nodes?.some(n=>n.skin!==undefined)||json.meshes?.some(m=>m.primitives?.some(p=>Object.keys(p.attributes||{}).some(k=>/^(JOINTS|WEIGHTS)_/.test(k)))))throw new Error('静态预览不能包含隐藏的骨架或动画。');if(!json.nodes?.some(n=>Number.isInteger(n.mesh)&&n.mesh>=0&&n.mesh<(json.meshes?.length||0)))throw new Error('静态预览没有实际网格。');return json;}
  if(!json.skins?.length)throw new Error('GLB 需要真实匹配骨架。');
  if(!json.animations?.length)throw new Error('GLB 尚无真实动画片段。');
  for(const skin of json.skins){const joints=skin.joints;if(!Array.isArray(joints)||!joints.length||new Set(joints).size!==joints.length||joints.some(j=>!Number.isInteger(j)||j<0||j>=json.nodes?.length))throw new Error('骨骼索引不完整。');}
  for(const node of json.nodes||[])if(node.skin!==undefined&&(!Number.isInteger(node.skin)||node.skin<0||node.skin>=json.skins.length||!Number.isInteger(node.mesh)||node.mesh<0||node.mesh>=(json.meshes?.length||0)))throw new Error('网格的骨架引用不完整。');
  if(!json.nodes?.some(n=>n.skin!==undefined&&Number.isInteger(n.mesh)))throw new Error('GLB 尚无绑定骨架的真实网格。');
  return json;
}

export class PreviewSeekGate {
  constructor(){this.intent=0;}
  cancel(){this.intent++;}
  async seek(viewer,context,time,unit,isCurrent=()=>true,{frame=false}={}){
    const intent=++this.intent,ready=await viewer.setContext(context);
    if(intent!==this.intent||!ready||!isCurrent()||viewer.context?.objectId!==context.objectId||viewer.context?.sequenceId!==context.sequenceId||!viewer.clip)return false;
    return frame?viewer.seekEventFrame(time,unit):viewer.seekAction(time,unit);
  }
}


export function animationDrivesRig(root,tracks) {
  if(!root||!Array.isArray(tracks))return false;
  const names=new Set(),inside=new Set();root.traverse(node=>inside.add(node));
  root.traverse(node=>{if(!node.isBone)return;for(let current=node;current&&inside.has(current);current=current.parent){if(current.name)names.add(current.name);if(current.uuid)names.add(current.uuid);}});
  return tracks.some(track=>track.name&&track.times?.length&&[...names].some(name=>track.name.startsWith(name+'.')));
}
