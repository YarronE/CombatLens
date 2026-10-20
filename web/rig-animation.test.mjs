import test from 'node:test';
import assert from 'node:assert/strict';
import {animationDrivesRig} from './preview-model.js';
const tree=()=>{const root={name:'model'},ancestor={name:'Root',parent:root},bone={name:'joint',isBone:true,parent:ancestor},helper={name:'attachment',parent:root};root.traverse=fn=>[root,ancestor,bone,helper].forEach(fn);return root;};
test('joint and its real ancestor both drive a rig',()=>{for(const name of ['joint.position','Root.quaternion'])assert.equal(animationDrivesRig(tree(),[{name,times:[0,1]}]),true);});
test('unrelated helper alone does not drive the rig',()=>assert.equal(animationDrivesRig(tree(),[{name:'attachment.position',times:[0,1]}]),false));
test('empty tracks and names sharing only a prefix stay rejected',()=>{assert.equal(animationDrivesRig(tree(),[{name:'RootMotion.position',times:[0,1]}]),false);assert.equal(animationDrivesRig(tree(),[{name:'joint.position',times:[]}]),false);});
