import {capturePointerGesture} from './timeline-edit.js';
import {splitFraction} from './editor-layout.js';
const editor=document.getElementById('action-editor'),divider=document.getElementById('editor-divider');
let share=.48;
function apply(value){share=Math.max(.25,Math.min(.75,value));editor.style.setProperty('--viewport-share',(share*100)+'%');divider.setAttribute('aria-valuenow',String(Math.round(share*100)))}
divider.addEventListener('pointerdown',event=>{if(event.button!==0)return;event.preventDefault();const previous=share,bounds=editor.getBoundingClientRect();capturePointerGesture(divider,event.pointerId,{onMove:e=>apply(splitFraction(e.clientY,bounds.top,bounds.height)),onEnd:commit=>{if(!commit)apply(previous)}})});
divider.addEventListener('keydown',event=>{if(!['ArrowUp','ArrowDown','Home','End'].includes(event.key))return;event.preventDefault();apply(event.key==='Home' ? .25 : event.key==='End' ? .75 : share+(event.key==='ArrowDown' ? .04 : -.04))});
apply(share);
