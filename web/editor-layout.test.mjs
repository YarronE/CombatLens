import test from 'node:test';
import assert from 'node:assert/strict';
import {splitFraction,timelineWidth,rulerTicks} from './editor-layout.js';
import {adjustedTiming} from './timeline-edit.js';
test('split clamps and rejects unavailable editor geometry',()=>{assert.equal(splitFraction(150,100,100),.5);assert.equal(splitFraction(-10,100,100),.25);assert.equal(splitFraction(900,100,100),.75);assert.throws(()=>splitFraction(1,0,0));assert.throws(()=>splitFraction(NaN,0,100))});
test('timeline fits available width while retaining a scrollable narrow axis',()=>{assert.equal(timelineWidth(954),952);assert.equal(timelineWidth(378),640);assert.equal(timelineWidth(954,2),1904);assert.equal(timelineWidth(NaN,Infinity),640);assert.equal(timelineWidth(954,99),3808)});
test('same native drag delta survives zoom and responsive width changes',()=>{for(const available of [378,954,1440])for(const zoom of [1,2,4]){const width=timelineWidth(available,zoom),pixels=(width-185-16)*.1,delta=pixels/(width-185-16)*5;assert.deepEqual(adjustedTiming({start:1,end:2},delta,'move',{low:0,high:5,step:.01}),{start:1.5,end:2.5})}});
test('ruler uses bounded readable ticks over fractional and negative ranges',()=>{assert.deepEqual(rulerTicks(0,1.55,750),[0,.2,.4,.6,.8,1,1.2,1.4]);const ticks=rulerTicks(-.23,.39,1000);assert.ok(ticks.every(t=>t>=-.23&&t<=.39));assert.ok(ticks.length<20);assert.ok(ticks.includes(0));assert.deepEqual(rulerTicks(1,1,500),[]);assert.deepEqual(rulerTicks(0,NaN,500),[])});

test('extreme finite ranges never emit nonfinite ruler coordinates',()=>{for(const [low,high] of [[0,Number.MIN_VALUE],[-Number.MAX_VALUE,Number.MAX_VALUE],[1e-320,2e-320]])assert.ok(rulerTicks(low,high,2000).every(Number.isFinite))});
