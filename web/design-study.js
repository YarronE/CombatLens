import {studyEvents,studyContext,intervals,StudyRequestGate} from './study-model.js';
import {unitLabel,valueText} from './model.js';
const node=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
const btn=(label,fn)=>{const b=node('button','',label);b.type='button';b.addEventListener('click',fn);return b;};
const labels={rhythm:'招式节奏',values:'范围与数值',phases:'阶段与选招'};
const kinds={configuration:'配置事实',observation:'实机观察',author_statement:'作者自述'};
export class DesignStudy{
 constructor(host,{request,selectEvent,openSource}){this.host=host;this.request=request;this.selectEvent=selectEvent;this.openSource=openSource;this.view='rhythm';this.gate=new StudyRequestGate();this.key=null;this.data=null;this.selected=null;}
 update({source,object,sequence,mode,stale,selected}){this.context={source,object,sequence,mode,stale};this.selected=selected;const key=JSON.stringify([source?.package_fingerprint,object?.id,sequence?.id,mode,stale]);if(key===this.key){this.markSelection();return;}this.key=key;this.track=sequence?.study_focus_track||'';this.data=null;this.draw();this.gate.load(key,()=>this.request('/api/design-study'),data=>{this.data=data;this.draw();});}
 refresh(){this.data=null;this.draw();this.gate.load(this.key,()=>this.request('/api/design-study'),data=>{this.data=data;this.draw();});}
 markSelection(){for(const b of this.host.querySelectorAll('[data-study-event]'))b.setAttribute('aria-pressed',String(b.dataset.studyEvent===this.selected));}
 draw(){const {source,object,sequence,mode,stale}=this.context||{};this.host.replaceChildren();if(!sequence)return;
  const header=node('div','study-heading');header.append(node('h2','','设计解读'),btn('核对证据',()=>this.refresh()));this.host.append(header);
  const tabs=node('div','study-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','设计解读视图');
  for(const [id,label] of Object.entries(labels)){const b=btn(label,()=>{this.view=id;this.draw();});b.id='study-tab-'+id;b.setAttribute('role','tab');b.setAttribute('aria-selected',String(id===this.view));b.setAttribute('aria-controls','study-panel');b.tabIndex=id===this.view?0:-1;b.addEventListener('keydown',e=>{const keys=Object.keys(labels);if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();this.view=e.key==='Home'?keys[0]:e.key==='End'?keys[2]:keys[(keys.indexOf(id)+(e.key==='ArrowRight'?1:2))%3];this.draw();this.host.querySelector('#study-tab-'+this.view).focus();}});tabs.append(b);}this.host.append(tabs);
  const panel=node('section','study-panel');panel.id='study-panel';panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby','study-tab-'+this.view);this.host.append(panel);
  if(mode==='analysis')panel.append(node('p','study-note','本页解读原始配置；分析副本中的修改属于假设。切回原始事件后可从本页定位模型。'));
  if(!this.data){panel.append(node('p','muted','正在核对当前动作的证据…'));return;}
  if(stale){panel.append(node('p','study-gap','当前副本来源已变化，设计解读暂不可用。'));return;}
  const entry=studyContext(this.data,source,object,sequence);
  if(!entry){panel.append(node('p','study-gap',this.data.diagnostic||'当前动作尚未登记设计解读。原始事件和动画仍可查看。'));return;}
  if(this.view==='rhythm')this.rhythm(panel,sequence,mode);
  const facts=entry.facts.filter(f=>f.view===this.view);
  if(this.view==='values')panel.append(node('p','study-note','下列数值保留配置单位；缺少挂点和变换依据时不叠加到模型。'));
  if(this.view==='phases')panel.append(node('p','study-note','条件与分支按来源分别展示，不据此推定实际选招概率。'));
  for(const f of facts){const card=node('article','study-fact');card.append(node('span','study-kind',kinds[f.kind]),node('h3','',f.label));card.append(node('pre',f.status==='ready'?'study-value':'study-gap',f.status==='ready'?valueText(f.value):f.reason||'未确认'));if(f.unit)card.append(node('span','study-unit',f.unit));card.append(node('p','study-note',f.note));const proof=node('details');proof.append(node('summary','','字段与来源'),node('code','',f.pointer||'定位未知'),btn('查看原始来源',()=>this.openSource(f.source_id)));card.append(proof);panel.append(card);}
  for(const c of entry.calculations.filter(c=>c.view===this.view)){const card=node('div','study-fact');card.append(node('span','study-kind','计算结果'),node('h3','',c.label),node('p','study-value',c.status==='ready'?Number(c.value.toPrecision(7))+' '+c.unit:c.reason),node('p','study-note','依据 '+c.inputs.join('、')));panel.append(card);}
  for(const h of entry.hypotheses.filter(h=>h.view===this.view)){const card=node('article','study-hypothesis');card.append(node('span','study-kind',h.status==='hypothesis'?'分析假设':'证据缺口'),node('p','',h.text),node('p','study-note',h.validation));panel.append(card);}
  if(!facts.length&&this.view!=='rhythm')panel.append(node('p','study-gap','这个动作尚无可确认的对应字段。'));
  if(entry.gaps.length){const gaps=node('details','study-gaps');gaps.open=true;gaps.append(node('summary','','证据缺口'));const ul=node('ul');entry.gaps.forEach(g=>ul.append(node('li','',g)));gaps.append(ul);panel.append(gaps);}this.markSelection();
 }
 rhythm(panel,sequence,mode){const all=studyEvents(sequence,this.data.affected_event_ids),tracks=[...new Set(all.known.map(e=>e.track))];if(this.track&&!tracks.includes(this.track))this.track='';const filter=node('select');filter.setAttribute('aria-label','设计解读轨道');for(const track of ['',...tracks]){const option=node('option','',track||'全部轨道');option.value=track;filter.append(option);}filter.value=this.track;filter.addEventListener('change',()=>{this.track=filter.value;this.draw();});panel.append(filter);const known=all.known.filter(e=>!this.track||e.track===this.track),unknown=all.unknown;panel.append(node('h3','',known.length+' 个已确认坐标 · '+unknown.length+' 个待确认'));
  if(known.length){const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 380 70');svg.setAttribute('role','img');svg.setAttribute('aria-label','事件起点分布，'+unitLabel(sequence.unit));const min=Math.min(0,known[0].start),max=Math.max(1,...known.map(e=>e.start));const add=(tag,attrs,text)=>{const n=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;svg.append(n);};add('line',{x1:16,x2:364,y1:28,y2:28,stroke:'#687784'});known.forEach(e=>add('circle',{cx:16+(e.start-min)/(max-min)*348,cy:28,r:3,fill:'#d4c778'}));add('text',{x:16,y:57,fill:'#bcc8d0','font-size':12},String(min));add('text',{x:364,y:57,fill:'#bcc8d0','font-size':12,'text-anchor':'end'},max+' '+unitLabel(sequence.unit));panel.append(svg);
   const gaps=intervals(known),nonzero=gaps.filter(g=>g.value>0);if(nonzero.length)panel.append(node('p','study-note','相邻起点间隔 '+Math.min(...nonzero.map(g=>g.value)).toFixed(3)+'–'+Math.max(...nonzero.map(g=>g.value)).toFixed(3)+' '+unitLabel(sequence.unit)+'。该间隔不自动代表应对窗口。'));
  }
  const list=node('div','study-events');for(const e of known){const b=btn(e.label+' · '+e.start+' '+unitLabel(e.unit),()=>this.selectEvent(e.id,true));b.dataset.studyEvent=e.id;b.disabled=mode==='analysis';list.append(b);}panel.append(list);
  if(unknown.length){const details=node('details','study-gaps');details.append(node('summary','','时间或来源未确认 · '+unknown.length));for(const e of unknown){const b=btn(e.label+' · 查看证据',()=>this.selectEvent(e.id,false));b.dataset.studyEvent=e.id;b.disabled=mode==='analysis';details.append(b);}panel.append(details);}
 }
}
