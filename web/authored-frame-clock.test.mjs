import test from 'node:test';
import assert from 'node:assert/strict';
import {clockMapping,actionToClip,clipToAction,PlaybackClock} from './preview-model.js';
import {eventFrameTarget} from './frame-model.js';
const clip={clip_duration_seconds:2,sample_times_seconds:[0,.5,1,1.5,2],clock_mapping:{status:'proven',unit:'frames',action_in:0,action_out:48,clip_in:0,clip_out:2,play_rate:1,seconds_per_unit:1/24,source_ids:['synthetic-source']}};
test('authored coordinates are independent of registered sample rate and playback speed',()=>{
 assert.equal(actionToClip(24,'frames',clip),1);assert.equal(clipToAction(1,clip),24);
 assert.equal(eventFrameTarget(clip,13,'frames').index,2);
 const clock=new PlaybackClock();clock.configure(2,clockMapping(clip).play_rate);clock.toggle();clock.tick(.5);assert.equal(clock.time,.5);
 assert.equal(actionToClip(24,'seconds',clip),null);
});
test('authored scale must be explicit, positive and dimensionally consistent',()=>{
 for(const value of [undefined,0,-1,Infinity,1/30])assert.equal(clockMapping({...clip,clock_mapping:{...clip.clock_mapping,seconds_per_unit:value}}),null);
 assert.equal(clockMapping({...clip,clock_mapping:{...clip.clock_mapping,unit:'source_units'}}),null);
 assert.equal(clockMapping({...clip,clock_mapping:{...clip.clock_mapping,unit:'seconds',seconds_per_unit:1/24}}),null);
});

test('float32 source-length rounding does not skip the intended sample',()=>{
 const rounded={clip_duration_seconds:4,sample_times_seconds:[0,3.1,4],clock_mapping:{...clip.clock_mapping,action_out:240,clip_out:4,seconds_per_unit:1/60}};
 assert.equal(eventFrameTarget(rounded,186.000012,'frames').index,1);
});

import {AssetViewer} from './viewer.js';
test('viewer preserves authored-frame range while looping and stepping real samples',()=>{
 const viewer=Object.create(AssetViewer.prototype);viewer.clip=clip;viewer.clock=new PlaybackClock();viewer.clock.configure(2,1);viewer.frames=clip.sample_times_seconds;
 viewer.options={onPlayback:()=>{}};viewer.refreshPlaybackControls=()=>{};viewer.updateControls=()=>{};
 viewer.setActionRange(12,36);assert.deepEqual(viewer.clock.range,{start:.5,end:1.5});
 viewer.clock.loop=true;viewer.clock.toggle();viewer.clock.tick(1.25);assert.equal(viewer.clock.time,.75);
 viewer.step(1);assert.equal(viewer.clock.time,1);assert.equal(clipToAction(viewer.clock.time,clip),24);
 const result=viewer.seekEventFrame(13,'frames');assert.equal(result.index,2);assert.equal(viewer.clock.playing,false);
});
