"""Synthetic GLB security/clock fixtures stay inside disposable tests."""
import hashlib
import json
import struct
import unittest
from unittest.mock import patch
import test_server
from combatlens.runtime.preview import PreviewRepository
import combatlens.runtime.preview as preview_module
from combatlens.runtime.validation import WorkbenchError


def fixture(uri=None, mutate=None, times=(0.0, 1.0)):
    # One triangle, one joint and a real two-key translation channel. All test
    # geometry and animation are synthetic; no original game content is used.
    binary = b''.join([
        struct.pack('<9f', 0,0,0, 1,0,0, 0,1,0),
        struct.pack('<12H', *([0,0,0,0] * 3)),
        struct.pack('<12f', *([1,0,0,0] * 3)),
        struct.pack('<2f', *times),
        struct.pack('<6f', 0,0,0, 1,0,0),
    ])
    doc = {
        'asset': {'version':'2.0', 'generator':'synthetic-only preview test'},
        'buffers': [{'byteLength':len(binary)}],
        'bufferViews': [{'buffer':0,'byteOffset':offset,'byteLength':length} for offset,length in [(0,36),(36,24),(60,48),(108,8),(116,24)]],
        'accessors': [
            {'bufferView':0,'componentType':5126,'count':3,'type':'VEC3','min':[0,0,0],'max':[1,1,0]},
            {'bufferView':1,'componentType':5123,'count':3,'type':'VEC4'},
            {'bufferView':2,'componentType':5126,'count':3,'type':'VEC4'},
            {'bufferView':3,'componentType':5126,'count':2,'type':'SCALAR','min':[0],'max':[1]},
            {'bufferView':4,'componentType':5126,'count':2,'type':'VEC3'},
        ],
        'nodes': [{'mesh':0,'skin':0}, {'name':'synthetic-bone'}],
        'skins': [{'joints':[1],'skeleton':1}],
        'meshes': [{'primitives':[{'attributes':{'POSITION':0,'JOINTS_0':1,'WEIGHTS_0':2}}]}],
        'animations': [{'name':'synthetic-clip','samplers':[{'input':3,'output':4,'interpolation':'LINEAR'}], 'channels':[{'sampler':0,'target':{'node':1,'path':'translation'}}]}],
        'scenes': [{'nodes':[0,1]}], 'scene':0,
    }
    if uri is not None: doc['buffers'][0]['uri']=uri
    if mutate is not None: mutate(doc)
    raw=json.dumps(doc,separators=(',',':')).encode()
    raw+=b' '*(-len(raw)%4)
    length=12+8+len(raw)+8+len(binary)
    return struct.pack('<5I',0x46546c67,2,length,len(raw),0x4e4f534a)+raw+struct.pack('<2I',len(binary),0x004e4942)+binary


class PreviewTests(unittest.TestCase):
    tearDown = test_server.WorkbenchTests.tearDown
    # Reuse setup only; inherited behavioral tests remain in test_server.
    def setUp(self):
        test_server.WorkbenchTests.setUp(self)
        self.preview_dir=self.root/'local/preview'
        self.preview_dir.mkdir()
        self.glb=self.preview_dir/'synthetic.glb'
        self.glb.write_bytes(fixture())
        self.manifest={'schema_version':'preview-source/1','game_build':'synthetic-build','package_fingerprint':self.fingerprint,'assets':[{'id':'synthetic-only','object_id':'character-one','sequence_ids':['sequence-one'],'status':'ready','local_path':'synthetic.glb','format':'glb','bytes':self.glb.stat().st_size,'sha256':hashlib.sha256(self.glb.read_bytes()).hexdigest(),'source_ids':['source-one'],'clips':[{'id':'synthetic-clip','name':'synthetic-clip','animation_index':0,'clip_duration_seconds':1,'source_ids':['source-one'],'clock_mapping':{'status':'proven','unit':'seconds','action_in':0,'action_out':1,'clip_in':0,'clip_out':1,'play_rate':1,'source_ids':['source-one']}}]}]}
        self.preview=PreviewRepository(self.repository)
        self.write_manifest()

    def write_manifest(self):
        (self.research/'preview.json').write_text(json.dumps(self.manifest),encoding='utf-8')

    def replace_glb(self, payload):
        self.glb.write_bytes(payload)
        self.manifest['assets'][0].update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        self.write_manifest()

    def test_registered_binary_and_path_redaction(self):
        public=self.preview.response()
        self.assertNotIn('local_path',public['assets'][0])
        with self.preview.binary('synthetic-only')[0] as f:
            self.assertEqual(f.read(),self.glb.read_bytes())

    def test_changed_hash_disables_playback(self):
        self.glb.write_bytes(self.glb.read_bytes()[:-1]+b'X')
        self.assertEqual(self.preview.response()['assets'][0]['status'],'changed')
        with self.assertRaises(WorkbenchError): self.preview.binary('synthetic-only')

    def test_path_escape_and_external_resource_rejected(self):
        self.manifest['assets'][0]['local_path']='../research/original.json'
        self.write_manifest()
        self.assertEqual(self.preview.response()['assets'][0]['status'],'unavailable')
        self.manifest['assets'][0]['local_path']='synthetic.glb'
        self.glb.write_bytes(fixture('https://example.invalid/remote.bin'))
        self.manifest['assets'][0].update(bytes=self.glb.stat().st_size,sha256=hashlib.sha256(self.glb.read_bytes()).hexdigest())
        self.write_manifest()
        self.assertEqual(self.preview.response()['assets'][0]['status'],'unavailable')

    def test_stale_source_disables_clock_and_binary(self):
        self.snapshot.write_text('{"changed":true}',encoding='utf-8')
        self.assertEqual(self.preview.response()['assets'][0]['status'],'changed')
        with self.assertRaises(WorkbenchError): self.preview.binary('synthetic-only')

    def test_invalid_clock_and_stale_package_rejected(self):
        self.manifest['assets'][0]['clips'][0]['clock_mapping']['play_rate']=2
        self.write_manifest()
        with self.assertRaises(WorkbenchError): self.preview.response()
        self.manifest['assets'][0]['clips'][0]['clock_mapping']['play_rate']=1
        self.manifest['package_fingerprint']='0'*64
        self.write_manifest()
        with self.assertRaises(WorkbenchError) as caught:
            self.preview.response()
        self.assertEqual(caught.exception.code,'stale_preview_manifest')

    def test_invalid_joint_empty_geometry_and_empty_animation_cannot_be_ready(self):
        cases = {
            'out-of-range joint': lambda d:d['skins'][0].update(joints=[999]),
            'empty geometry': lambda d:d['meshes'][0].update(primitives=[]),
            'empty animation': lambda d:d['animations'][0].update(samplers=[],channels=[]),
            'channel targets non-joint mesh': lambda d:d['animations'][0]['channels'][0]['target'].update(node=0),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                self.replace_glb(fixture(mutate=mutate))
                self.assertEqual(self.preview.response()['assets'][0]['status'],'unavailable')
                with self.assertRaises(WorkbenchError) as caught:
                    self.preview.binary('synthetic-only')
                self.assertEqual(caught.exception.status,503)

    def test_clock_outside_real_clip_and_nonobject_mapping_are_rejected(self):
        mapping=self.manifest['assets'][0]['clips'][0]['clock_mapping']
        mapping.update(action_out=999,clip_out=999)
        self.write_manifest()
        with self.assertRaises(WorkbenchError) as caught:
            self.preview.manifest()
        self.assertEqual(caught.exception.status,503)
        self.manifest['assets'][0]['clips'][0]['clock_mapping']=[]
        self.write_manifest()
        with self.assertRaises(WorkbenchError) as caught:
            self.preview.manifest()
        self.assertEqual(caught.exception.status,503)

    def test_manifest_duration_must_match_real_animation_keys(self):
        self.manifest['assets'][0]['clips'][0]['clip_duration_seconds']=2
        self.write_manifest()
        self.assertEqual(self.preview.response()['assets'][0]['status'],'unavailable')
        with self.assertRaises(WorkbenchError) as caught:
            self.preview.binary('synthetic-only')
        self.assertEqual(caught.exception.status,503)

    def test_clock_cannot_exceed_known_authored_action_duration(self):
        self.originals['objects'][0]['sequences'][0].update(unit='seconds',duration=0.5)
        (self.research/'timelines.json').write_text(json.dumps(self.originals),encoding='utf-8')
        with self.assertRaises(WorkbenchError) as caught:
            self.preview.manifest()
        self.assertEqual(caught.exception.status,503)

    def test_binary_animation_keys_and_accessor_ranges_are_validated(self):
        invalid_vertex_joint=bytearray(fixture())
        bin_start=28+struct.unpack_from('<I',invalid_vertex_joint,12)[0]
        struct.pack_into('<H',invalid_vertex_joint,bin_start+36,999)
        cases = [
            fixture(times=(0.0,0.0)),
            fixture(times=(0.0,float('nan'))),
            # JSON min/max still claim 0..1, but actual BIN ends at 2 seconds.
            fixture(times=(0.0,2.0)),
            bytes(invalid_vertex_joint),
            fixture(mutate=lambda d:d['bufferViews'][3].update(byteOffset=10000)),
            fixture(mutate=lambda d:d['accessors'][3].update(count=10000)),
        ]
        for payload in cases:
            with self.subTest(payload_sha256=hashlib.sha256(payload).hexdigest()):
                self.replace_glb(payload)
                self.assertEqual(self.preview.response()['assets'][0]['status'],'unavailable')
                with self.assertRaises(WorkbenchError) as caught:
                    self.preview.binary('synthetic-only')
                self.assertEqual(caught.exception.status,503)

    def test_open_handle_identity_caches_validation_and_detects_replacement(self):
        with patch.object(preview_module.hashlib,'file_digest',wraps=hashlib.file_digest) as digest, patch.object(preview_module,'inspect_glb',wraps=preview_module.inspect_glb) as inspect, patch.object(preview_module.os,'fstat',wraps=preview_module.os.fstat) as stat:
            self.assertEqual(self.preview.response()['assets'][0]['status'],'ready')
            with self.preview.binary('synthetic-only')[0] as handle:
                self.assertEqual(handle.read(),self.glb.read_bytes())
            self.assertEqual(digest.call_count,1)
            self.assertEqual(inspect.call_count,1)
            self.assertGreaterEqual(stat.call_count,4)
            # Same pathname, different opened file identity: reject changed hash.
            replacement=self.preview_dir/'replacement.glb'
            replacement.write_bytes(fixture(times=(0.0,2.0)))
            replacement.replace(self.glb)
            self.assertEqual(self.preview.response()['assets'][0]['status'],'changed')
            self.assertEqual(digest.call_count,2)

    def test_binary_host_origin_and_unknown_id(self):
        from urllib.request import Request,urlopen
        from urllib.error import HTTPError
        with urlopen(Request(self.base+'/api/preview/assets/synthetic-only',headers={'Origin':self.base}),timeout=3) as r:
            self.assertEqual(r.headers['Content-Type'],'model/gltf-binary')
            self.assertEqual(r.read(),self.glb.read_bytes())
        for aid in ['unknown','%2e%2e%2fsecret']:
            with self.assertRaises(HTTPError): urlopen(self.base+'/api/preview/assets/'+aid,timeout=3)
        with self.assertRaises(HTTPError) as caught:
            urlopen(Request(self.base+'/api/preview/assets/synthetic-only',headers={'Origin':'https://example.invalid'}),timeout=3)
        self.assertEqual(caught.exception.code,403)


if __name__=='__main__': unittest.main()


def static_fixture(mutate=None):
    def change(doc):
        doc.pop('skins');doc.pop('animations');doc['nodes']=[{'mesh':0}];doc['scenes']=[{'nodes':[0]}]
        doc['meshes'][0]['primitives'][0]['attributes']={'POSITION':0}
        if mutate:mutate(doc)
    return fixture(mutate=change)

class StaticOnlyTests(unittest.TestCase):
    setUp=PreviewTests.setUp
    tearDown=PreviewTests.tearDown
    replace_glb=PreviewTests.replace_glb
    write_manifest=PreviewTests.write_manifest
    def static(self,raw=None):
        self.manifest['assets'][0].update(kind='static_mesh',clips=[])
        self.replace_glb(raw or static_fixture())
    def test_explicit_static_geometry_has_no_animation_clock(self):
        self.static();asset=self.preview.response()['assets'][0];self.assertEqual(asset['status'],'ready');self.assertEqual(asset['clips'],[])
        handle,_,_=self.preview.binary('synthetic-only');handle.close()
    def test_static_kind_cannot_hide_rig_animation_or_skin_attributes(self):
        for mutate in [lambda d:d.update(skins=[{'joints':[0]}]),lambda d:d.update(animations=[{}]),lambda d:d['nodes'][0].update(skin=0),lambda d:d['meshes'][0]['primitives'][0]['attributes'].update(JOINTS_0=1)]:
            self.static(static_fixture(mutate));self.assertEqual(self.preview.response()['assets'][0]['status'],'unavailable')
    def test_default_mode_remains_strict_and_mode_changes_invalidate_cached_doc(self):
        self.static();self.assertEqual(self.preview.response()['assets'][0]['status'],'ready')
        self.manifest['assets'][0].pop('kind');self.manifest['assets'][0]['clips']=[{'id':'x','name':'synthetic-clip','animation_index':0,'clip_duration_seconds':1,'source_ids':['source-one']}]
        # Missing rig remains invalid even if its same path/bytes were cached as static.
        self.write_manifest();self.assertNotEqual(self.preview.response()['assets'][0]['status'],'ready')
    def test_static_empty_invalid_geometry_is_rejected(self):
        for mutate in [lambda d:d['meshes'][0].update(primitives=[]),lambda d:d['accessors'][0].update(count=1000),lambda d:d['nodes'][0].update(children=[0]),lambda d:d['scenes'][0].update(nodes=[])]:
            self.static(static_fixture(mutate));self.assertEqual(self.preview.response()['assets'][0]['status'],'unavailable')


class RigHierarchyTests(unittest.TestCase):
    def inspect(self,mutate):
        import io
        payload=fixture(mutate=mutate)
        return preview_module.inspect_glb(io.BytesIO(payload),len(payload))

    def test_real_rig_root_ancestor_is_allowed(self):
        def mutate(d):
            d['nodes'].append({'name':'source-root','children':[1]})
            d['scenes'][0]['nodes']=[0,2]
            d['animations'][0]['channels'][0]['target']['node']=2
        self.assertEqual(self.inspect(mutate)['_workbench_animation_bounds'][0]['last'],1)

    def test_joint_with_additional_reachable_helper_is_allowed(self):
        def mutate(d):
            d['nodes'].append({'name':'attachment'})
            d['scenes'][0]['nodes'].append(2)
            d['animations'][0]['channels'].append({'sampler':0,'target':{'node':2,'path':'translation'}})
        self.assertEqual(len(self.inspect(mutate)['animations'][0]['channels']),2)

    def test_helper_only_and_out_of_scene_channels_are_rejected(self):
        for reachable in [False,True]:
            def mutate(d):
                d['nodes'].append({'name':'unrelated'})
                if reachable:d['scenes'][0]['nodes'].append(2)
                else:d['animations'][0]['channels'].append({'sampler':0,'target':{'node':1,'path':'scale'}})
                d['animations'][0]['channels'][0]['target']['node']=2
            with self.subTest(reachable=reachable),self.assertRaises(ValueError):self.inspect(mutate)


class MultiSkinTests(unittest.TestCase):
    inspect = RigHierarchyTests.inspect
    def test_independent_skin_joint_sets_are_preserved(self):
        def mutate(d):
            d['nodes'].extend([{'name':'second-joint'},{'mesh':0,'skin':1}])
            d['skins'].append({'joints':[2]})
            d['scenes'][0]['nodes'].extend([2,3])
        self.assertEqual(len(self.inspect(mutate)['skins']),2)

    def test_each_skin_binding_checks_vertex_indices_and_matrix_count(self):
        import io
        def mutate(d):
            d['nodes'].extend([{'name':'second-joint'},{'mesh':0,'skin':1}])
            d['skins'].append({'joints':[1,2]})
            d['scenes'][0]['nodes'].extend([2,3])
        raw=bytearray(fixture(mutate=mutate));start=28+struct.unpack_from('<I',raw,12)[0]
        struct.pack_into('<H',raw,start+36,1)
        with self.assertRaises(ValueError):preview_module.inspect_glb(io.BytesIO(raw),len(raw))
        def bad_skin(d):d['nodes'][0]['skin']=5
        with self.assertRaises(ValueError):self.inspect(bad_skin)
