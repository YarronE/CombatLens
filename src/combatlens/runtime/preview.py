"""Registered, hash-checked local GLB previews. No user-supplied paths."""
from __future__ import annotations
import copy
import hashlib
import json
import math
import os
import re
import struct
from pathlib import Path
from .repository import read_json, within
from .validation import WorkbenchError

ASSET_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
MAX_GLB = 512 * 1024 * 1024
MAX_JSON = 8 * 1024 * 1024
TIME_TOLERANCE = 1e-5
COMPONENTS = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}


def integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Expected a bounded nonnegative integer.')
    return value


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def objects(value, label, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f'{label} must be an array of objects.')
    return value


def inspect_glb(handle, size, kind="skinned_animation"):
    """Check embedded bytes, geometry, rig and joint animation without execution.

    Accessor values are read in bounded batches, including interleaved vertices.
    JSON min/max is never used as proof of animation keys or vertex bounds.
    The private bounds added to the returned document are recomputed from BIN.
    """
    if kind not in {'skinned_animation','static_mesh'}:raise ValueError('Unsupported preview kind.')
    static=kind=='static_mesh'
    handle.seek(0)
    header = handle.read(20)
    if len(header) != 20:
        raise ValueError('Truncated GLB header.')
    magic, version, length, json_length, chunk_type = struct.unpack('<5I', header)
    if (magic, version, length, chunk_type) != (0x46546c67, 2, size, 0x4e4f534a) or json_length > MAX_JSON or json_length % 4 or 28 + json_length > size:
        raise ValueError('Invalid GLB header or JSON bound.')
    doc = json.loads(handle.read(json_length).decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite GLB JSON')))
    if not isinstance(doc, dict) or not isinstance(doc.get('asset'), dict) or doc['asset'].get('version') != '2.0' or doc.get('extensionsRequired'):
        raise ValueError('Unsupported glTF version or required decoder extension.')
    buffers = objects(doc.get('buffers'), 'buffers', True)
    images = objects(doc.get('images', []), 'images')
    if len(buffers) != 1 or any('uri' in item for item in buffers + images):
        raise ValueError('Preview must contain exactly one embedded buffer and no external resources.')
    chunk = handle.read(8)
    if len(chunk) != 8:
        raise ValueError('Missing GLB BIN chunk.')
    bin_length, bin_type = struct.unpack('<2I', chunk)
    bin_start = handle.tell()
    if bin_type != 0x004e4942 or bin_length % 4 or bin_start + bin_length != size:
        raise ValueError('Invalid GLB BIN bounds.')
    declared = integer(buffers[0].get('byteLength'), 1)
    if not 0 <= bin_length - declared <= 3:
        raise ValueError('Embedded buffer length mismatch.')
    views = objects(doc.get('bufferViews'), 'bufferViews', True)
    for view in views:
        offset, count = integer(view.get('byteOffset', 0)), integer(view.get('byteLength'), 1)
        if type(view.get('buffer')) is not int or view['buffer'] != 0 or offset + count > declared:
            raise ValueError('BufferView exceeds the actual embedded buffer.')
        if 'byteStride' in view:
            stride = integer(view['byteStride'], 4)
            if stride > 252 or stride % 4:
                raise ValueError('Invalid interleaved bufferView stride.')
    for image in images:
        image_index = integer(image.get('bufferView'))
        if image_index >= len(views):
            raise ValueError('Embedded image points outside bufferViews.')
    accessors = objects(doc.get('accessors'), 'accessors', True)
    layouts = []
    for accessor in accessors:
        index = integer(accessor.get('bufferView'))
        component = integer(accessor.get('componentType'))
        kind = accessor.get('type')
        if index >= len(views) or component not in COMPONENTS or not isinstance(kind, str) or kind not in WIDTHS or 'sparse' in accessor:
            raise ValueError('Unsupported or invalid accessor layout.')
        if kind.startswith('MAT') and component != 5126:
            raise ValueError('Padded integer matrix accessors are unsupported.')
        if 'normalized' in accessor and type(accessor['normalized']) is not bool:
            raise ValueError('Invalid accessor normalization flag.')
        if accessor.get('normalized') and component in (5125, 5126):
            raise ValueError('This accessor component cannot be normalized.')
        code, width = COMPONENTS[component]
        packed = width * WIDTHS[kind]
        view = views[index]
        offset = integer(accessor.get('byteOffset', 0))
        count = integer(accessor.get('count'), 1)
        stride = view.get('byteStride', packed)
        if offset % width or (view.get('byteOffset', 0) + offset) % width or stride % width or stride < packed or offset + (count - 1) * stride + packed > view['byteLength']:
            raise ValueError('Accessor exceeds its bufferView or has invalid alignment.')
        layouts.append((bin_start + view.get('byteOffset', 0) + offset, count, stride, packed, struct.Struct('<' + code * WIDTHS[kind])))

    def accessor_at(index, kind=None, components=None):
        index = integer(index)
        if index >= len(accessors):
            raise ValueError('Accessor index is outside accessors.')
        accessor = accessors[index]
        if kind is not None and accessor['type'] != kind or components is not None and accessor['componentType'] not in components:
            raise ValueError('Accessor type does not match its use.')
        return index, accessor

    def rows(index):
        start, count, stride, packed, decoder = layouts[index]
        for first in range(0, count, 4096):
            batch = min(4096, count - first)
            handle.seek(start + first * stride)
            raw = handle.read((batch - 1) * stride + packed)
            if len(raw) != (batch - 1) * stride + packed:
                raise ValueError('Truncated actual accessor bytes.')
            for position in range(batch):
                yield decoder.unpack_from(raw, position * stride)

    # Any float accessor used by the viewer must contain finite actual values.
    # This also checks animation outputs and inverse-bind matrices.
    for index, accessor in enumerate(accessors):
        if accessor['componentType'] == 5126 and any(not all(math.isfinite(value) for value in row) for row in rows(index)):
            raise ValueError('Nonfinite actual accessor values.')
    nodes = objects(doc.get('nodes'), 'nodes', True)
    meshes = objects(doc.get('meshes'), 'meshes', True)
    joints=[];joint_set=set()
    if static:
        if doc.get('skins') or doc.get('animations') or any('skin' in n for n in nodes):raise ValueError('Static previews cannot contain rigs or animation.')
        if not any('mesh' in n for n in nodes):raise ValueError('Static previews require a mesh node.')
    else:
        skins = objects(doc.get('skins'), 'skins', True)
        skin_joints=[]
        joint_set=set()
        for skin in skins:
            joints=skin.get('joints')
            if not isinstance(joints,list) or not joints or any(type(joint) is not int or not 0<=joint<len(nodes) for joint in joints) or len(set(joints))!=len(joints):
                raise ValueError('Skin joint indices are invalid or duplicate.')
            skin_joints.append(joints);joint_set.update(joints)
            if 'skeleton' in skin and integer(skin['skeleton'])>=len(nodes):
                raise ValueError('Skin skeleton is outside nodes.')
            if 'inverseBindMatrices' in skin:
                _,accessor=accessor_at(skin['inverseBindMatrices'],'MAT4',(5126,))
                if accessor['count']!=len(joints):
                    raise ValueError('Inverse-bind matrix count differs from joints.')
    parents = {}
    bound_meshes = {}
    for index, node in enumerate(nodes):
        children = node.get('children', [])
        if not isinstance(children, list):
            raise ValueError('Node children must be an array.')
        for child in children:
            child = integer(child)
            if child >= len(nodes) or child == index or child in parents:
                raise ValueError('Invalid node hierarchy.')
            parents[child] = index
        for key, width in (('translation', 3), ('rotation', 4), ('scale', 3), ('matrix', 16)):
            if key in node and (not isinstance(node[key], list) or len(node[key]) != width or not all(finite(value) for value in node[key])):
                raise ValueError('Invalid node transform.')
        if 'matrix' in node and any(key in node for key in ('translation', 'rotation', 'scale')):
            raise ValueError('Node cannot combine matrix and TRS.')
        if 'mesh' in node:
            mesh = integer(node['mesh'])
            if mesh >= len(meshes):
                raise ValueError('Node mesh is outside meshes.')
            if 'skin' in node:
                skin_index=integer(node['skin'])
                if static or skin_index>=len(skins):
                    raise ValueError('Node references an unsupported skin.')
                bound_meshes.setdefault(mesh,set()).add(skin_index)
        elif 'skin' in node:
            raise ValueError('Skin is not bound to mesh geometry.')
    if not static and not bound_meshes:
        raise ValueError('No mesh is bound to the preview skeleton.')
    visited = set()
    for start in range(len(nodes)):
        seen, current = set(), start
        while current not in visited and current is not None:
            if current in seen:
                raise ValueError('Node hierarchy contains a cycle.')
            seen.add(current)
            current = parents.get(current)
        visited.update(seen)
    scenes=objects(doc.get('scenes'), 'scenes', True)
    if integer(doc.get('scene',0))>=len(scenes):raise ValueError('Default scene is invalid.')
    for scene in scenes:
        roots=scene.get('nodes',[])
        if not isinstance(roots,list) or any(type(i) is not int or i<0 or i>=len(nodes) or i in parents for i in roots) or len(set(roots))!=len(roots):raise ValueError('Scene roots are invalid.')
    reachable=set();pending=list(scenes[doc.get('scene',0)].get('nodes',[]))
    while pending:
        node=pending.pop()
        if node in reachable:continue
        reachable.add(node);pending.extend(nodes[node].get('children',[]))
    if not any('mesh' in nodes[i] for i in reachable):raise ValueError('Active scene has no reachable mesh geometry.')
    for mesh_index, mesh in enumerate(meshes):
        primitives = objects(mesh.get('primitives'), 'mesh primitives', True)
        for primitive in primitives:
            attributes = primitive.get('attributes')
            if static and isinstance(attributes,dict) and any(k.startswith(('JOINTS_','WEIGHTS_')) for k in attributes):raise ValueError('Static previews cannot conceal skin attributes.')
            if not isinstance(attributes, dict):
                raise ValueError('Geometry requires attribute accessors.')
            position_index, position = accessor_at(attributes.get('POSITION'), 'VEC3', (5126,))
            if position['count'] < 3 or type(primitive.get('mode', 4)) is not int or not 0 <= primitive.get('mode', 4) <= 6:
                raise ValueError('Geometry must contain real vertices and a valid primitive mode.')
            for attribute_index in attributes.values():
                _, attribute = accessor_at(attribute_index)
                if attribute['count'] != position['count']:
                    raise ValueError('Geometry attribute counts differ.')
            if 'indices' in primitive:
                index, indices = accessor_at(primitive['indices'], 'SCALAR', (5121, 5123, 5125))
                if indices.get('normalized') or any(row[0] >= position['count'] for row in rows(index)):
                    raise ValueError('Actual primitive indices exceed the vertices.')
            if mesh_index in bound_meshes:
                index, joint_accessor = accessor_at(attributes.get('JOINTS_0'), 'VEC4', (5121, 5123))
                if joint_accessor.get('normalized') or any(any(joint >= min(len(skin_joints[skin_index]) for skin_index in bound_meshes[mesh_index]) for joint in row) for row in rows(index)):
                    raise ValueError('Actual vertex joint index exceeds the skin joints.')
                index, weights = accessor_at(attributes.get('WEIGHTS_0'), 'VEC4', (5121, 5123, 5126))
                if weights['componentType'] != 5126 and not weights.get('normalized'):
                    raise ValueError('Integer skin weights require normalization.')
                maximum = 1 if weights['componentType'] == 5126 else (255 if weights['componentType'] == 5121 else 65535)
                if any(any(value < 0 or value > maximum for value in row) or sum(row) <= 0 for row in rows(index)):
                    raise ValueError('Actual skin weights are invalid or empty.')
    animations = objects(doc.get('animations',[]) if static else doc.get('animations'), 'animations', not static)
    rig_nodes=set(joint_set) if not static else set()
    for joint in tuple(rig_nodes):
        current=parents.get(joint)
        while current is not None:
            rig_nodes.add(current);current=parents.get(current)
    time_bounds = {}
    animation_bounds = []
    for animation in animations:
        samplers = objects(animation.get('samplers'), 'animation samplers', True)
        channels = objects(animation.get('channels'), 'animation channels', True)
        used = set()
        drives_rig = False
        first, last = math.inf, -math.inf
        for channel in channels:
            sampler_index = integer(channel.get('sampler'))
            target = channel.get('target')
            if sampler_index >= len(samplers) or not isinstance(target, dict) or type(target.get('node')) is not int or target['node'] not in reachable or target.get('path') not in ('translation', 'rotation', 'scale'):
                raise ValueError('Animation channel must target an existing active-scene transform.')
            if 'matrix' in nodes[target['node']] or (target['node'], target['path']) in used:
                raise ValueError('Animated joint is a matrix or has duplicate channels.')
            used.add((target['node'], target['path']))
            drives_rig = drives_rig or target['node'] in rig_nodes
            sampler = samplers[sampler_index]
            input_index, input_accessor = accessor_at(sampler.get('input'), 'SCALAR', (5126,))
            if input_accessor.get('normalized'):
                raise ValueError('Animation time input cannot be normalized.')
            if input_index not in time_bounds:
                previous = None
                minimum = None
                for row in rows(input_index):
                    value = row[0]
                    if not math.isfinite(value) or value < 0 or previous is not None and value <= previous:
                        raise ValueError('Actual animation times must be finite and strictly increasing.')
                    if minimum is None:
                        minimum = value
                    previous = value
                time_bounds[input_index] = (minimum, previous)
            start, end = time_bounds[input_index]
            first, last = min(first, start), max(last, end)
            interpolation = sampler.get('interpolation', 'LINEAR')
            if interpolation not in ('LINEAR', 'STEP', 'CUBICSPLINE'):
                raise ValueError('Unsupported animation interpolation.')
            _, output = accessor_at(sampler.get('output'), 'VEC4' if target['path'] == 'rotation' else 'VEC3', (5126,))
            if output.get('normalized') or output['count'] != input_accessor['count'] * (3 if interpolation == 'CUBICSPLINE' else 1):
                raise ValueError('Animation output count differs from actual time keys.')
        if not drives_rig:
            raise ValueError('Animation must drive the registered rig or a rig ancestor.')
        if not math.isfinite(last) or last <= 0:
            raise ValueError('Animation has no positive actual clip duration.')
        animation_bounds.append({'first': first, 'last': last})
    doc['_workbench_animation_bounds'] = animation_bounds
    return doc


class PreviewRepository:
    def __init__(self, repository):
        self.repository = repository
        self.root = repository.root / 'local/preview'
        self.asset_cache = {}

    def manifest(self):
        package, fingerprint = self.repository.research()
        path = self.repository.research_dir / 'preview.json'
        if not path.exists():
            return {'schema_version':'preview-source/1', 'game_build':self.repository.timelines(fingerprint)['game_build'], 'package_fingerprint':fingerprint, 'assets':[]}
        manifest = read_json(path)[0]
        if not isinstance(manifest, dict) or manifest.get('schema_version') != 'preview-source/1' or not isinstance(manifest.get('assets'), list):
            raise WorkbenchError('Unsupported preview manifest.', status=503, code='invalid_preview_manifest')
        timeline = self.repository.timelines(fingerprint)
        if manifest.get('package_fingerprint') != fingerprint or manifest.get('game_build') != timeline['game_build']:
            raise WorkbenchError('Preview belongs to a different source package.', status=503, code='stale_preview_manifest')
        registered = {obj['id']: {seq['id']:seq for seq in obj['sequences']} for obj in timeline['objects']}
        sources = {source['id'] for source in package['sources']}
        def strings(value, label, nonempty=True):
            if not isinstance(value, list) or nonempty and not value or any(not isinstance(item, str) for item in value):
                raise ValueError(f'{label} must be an array of registered IDs.')
            return set(value)
        def source_ids(value):
            if not strings(value, 'Evidence sources') <= sources:
                raise ValueError('Preview requires registered evidence sources.')
        ids = set()
        try:
            for asset in objects(manifest['assets'], 'Preview assets'):
                aid = asset.get('id')
                if not isinstance(aid, str) or not ASSET_ID.fullmatch(aid) or aid in ids:
                    raise ValueError('Invalid or duplicate preview ID.')
                ids.add(aid)
                oid = asset.get('object_id')
                if not isinstance(oid, str) or oid not in registered or not strings(asset.get('sequence_ids'), 'Preview sequences') <= registered[oid].keys():
                    raise ValueError('Preview object or sequence is not registered.')
                source_ids(asset.get('source_ids'))
                kind=asset.get('kind','skinned_animation')
                if kind not in {'skinned_animation','static_mesh'}:raise ValueError('Unsupported preview kind.')
                if kind=='static_mesh' and asset.get('clips'):raise ValueError('Static preview cannot declare animation clips.')
                clips = objects(asset.get('clips', []), 'Preview clips', asset.get('status') == 'ready' and kind!='static_mesh')
                for clip in clips:
                    source_ids(clip.get('source_ids'))
                    if not isinstance(clip.get('name'), str) or not clip['name']:
                        raise ValueError('Clip name must match a registered animation.')
                    integer(clip.get('animation_index'))
                    duration = clip.get('clip_duration_seconds')
                    if not finite(duration) or duration <= 0:
                        raise ValueError('Clip duration requires a finite positive source value.')
                    mapping = clip.get('clock_mapping')
                    if mapping is not None:
                        names = ('action_in','action_out','clip_in','clip_out','play_rate')
                        if not isinstance(mapping, dict) or mapping.get('status') != 'proven' or mapping.get('unit') != 'seconds' or any(not finite(mapping.get(name)) for name in names):
                            raise ValueError('Invalid preview clock proof.')
                        if mapping['action_in'] < 0 or mapping['clip_in'] < 0 or mapping['action_out'] <= mapping['action_in'] or mapping['clip_out'] <= mapping['clip_in'] or mapping['play_rate'] <= 0 or mapping['clip_out'] > duration + TIME_TOLERANCE or not math.isclose(mapping['clip_out'] - mapping['clip_in'], (mapping['action_out'] - mapping['action_in']) * mapping['play_rate'], rel_tol=1e-9, abs_tol=TIME_TOLERANCE):
                            raise ValueError('Inconsistent or out-of-range preview clock mapping.')
                        for seqid in asset['sequence_ids']:
                            sequence = registered[oid][seqid]
                            if sequence.get('unit') == 'seconds' and finite(sequence.get('duration')) and mapping['action_out'] > sequence['duration'] + TIME_TOLERANCE:
                                raise ValueError('Preview clock mapping exceeds its authored action duration.')
                        source_ids(mapping.get('source_ids'))
        except (ValueError, TypeError, OverflowError) as error:
            raise WorkbenchError(str(error), status=503, code='invalid_preview_manifest') from error
        return manifest

    @staticmethod
    def stat_key(path, stat):
        return (str(path), stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)

    def open_asset(self, asset):
        text = asset.get('local_path')
        if not isinstance(text, str) or not text or '\x00' in text or '://' in text:
            raise WorkbenchError('No registered preview file.', status=404, code='preview_unavailable')
        candidate = Path(text)
        path = (candidate if candidate.is_absolute() else self.root / candidate).resolve()
        if not within(path, self.root.resolve()) or path.suffix.lower() != '.glb':
            raise WorkbenchError('Preview path is outside its local directory.', status=403, code='preview_path_rejected')
        try:
            handle = path.open('rb')
        except OSError as error:
            raise WorkbenchError('Registered preview is missing.', status=404, code='preview_unavailable') from error
        try:
            stat = os.fstat(handle.fileno())
            size = stat.st_size
            kind=asset.get('kind','skinned_animation')
            key = self.stat_key(path, stat)+(kind,)
            if not 20 <= size <= MAX_GLB or type(asset.get('bytes')) is not int or size != asset['bytes']:
                raise ValueError('Preview length changed or exceeds the bound.')
            cached = self.asset_cache.get(key)
            sha = cached[0] if cached else hashlib.file_digest(handle, 'sha256').hexdigest()
            if sha != asset.get('sha256'):
                raise WorkbenchError('Preview bytes changed.', status=409, code='preview_changed')
            doc = cached[1] if cached else inspect_glb(handle, size, kind)
            if self.stat_key(path, os.fstat(handle.fileno()))+(kind,) != key:
                raise WorkbenchError('Preview changed during validation.', status=409, code='preview_changed')
            for clip in asset.get('clips', []):
                index = clip['animation_index']
                if index >= len(doc['animations']) or doc['animations'][index].get('name') != clip.get('name'):
                    raise ValueError('Clip does not match the registered animation.')
                maximum = doc['_workbench_animation_bounds'][index]['last']
                if not math.isclose(maximum, clip['clip_duration_seconds'], rel_tol=1e-9, abs_tol=TIME_TOLERANCE):
                    raise ValueError('Registered duration differs from actual animation keys.')
                mapping = clip.get('clock_mapping')
                if mapping is not None and mapping['clip_out'] > maximum + TIME_TOLERANCE:
                    raise ValueError('Clock mapping exceeds actual animation keys.')
            # A file replacement invalidates its previous cached identity. Cache
            # contains only validated bytes and is never keyed by a path stat.
            if not cached:
                self.asset_cache = {old_key:value for old_key,value in self.asset_cache.items() if old_key[0] != str(path)}
                self.asset_cache[key] = (sha, doc)
            handle.seek(0)
            return handle, size, sha
        except WorkbenchError:
            handle.close()
            raise
        except (ValueError, KeyError, TypeError, UnicodeError, OSError, OverflowError, struct.error, RecursionError) as error:
            handle.close()
            raise WorkbenchError(str(error), status=503, code='invalid_preview_asset') from error

    def response(self):
        manifest = self.manifest()
        response = copy.deepcopy(manifest)
        validity = self.repository.validity()
        for original, asset in zip(manifest['assets'], response['assets']):
            asset.pop('local_path', None)
            if original.get('status') != 'ready':
                continue
            deps = set(original['source_ids'])
            for clip in original.get('clips', []):
                deps.update(clip.get('source_ids', []))
                deps.update((clip.get('clock_mapping') or {}).get('source_ids', []))
            if deps & set(validity['stale_source_ids']):
                asset.update(status='changed', reason='模型或时钟所依赖的证据已变化。')
                continue
            try:
                handle, _, _ = self.open_asset(original)
                handle.close()
            except WorkbenchError as error:
                asset.update(status='changed' if error.code == 'preview_changed' else 'unavailable', reason=str(error))
        response['validity'] = validity
        return response

    def binary(self, aid):
        if not isinstance(aid, str) or not ASSET_ID.fullmatch(aid):
            raise WorkbenchError('Invalid preview ID.', status=400, code='invalid_preview_id')
        manifest = self.manifest()
        asset = next((a for a in manifest['assets'] if a['id'] == aid), None)
        if asset is None:
            raise WorkbenchError('Unknown preview ID.', status=404, code='preview_unavailable')
        deps = set(asset['source_ids'])
        for clip in asset.get('clips', []):
            deps.update(clip.get('source_ids', []))
            deps.update((clip.get('clock_mapping') or {}).get('source_ids', []))
        if asset.get('status') != 'ready' or deps & set(self.repository.validity()['stale_source_ids']):
            raise WorkbenchError(asset.get('reason', 'Preview source is unavailable or changed.'), status=409, code='preview_unavailable')
        return self.open_asset(asset)
