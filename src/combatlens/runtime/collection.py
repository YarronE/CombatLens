"""Registered local workspace collections. Never accept paths from the browser."""
import re
from pathlib import Path
from .repository import Config, Repository, digest, read_json, within
from .preview import PreviewRepository
from .validation import WorkbenchError
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
SHA = re.compile(r'^[a-f0-9]{64}$')
class Collection:
    def __init__(self, repository):
        self.repository=repository;self.cache={}
    def entries(self):
        path=self.repository.research_dir/'workspaces.json'
        if not path.exists():return {'schema_version':'workspace-collection/1','entries':[]}
        if path.stat().st_size>512*1024:raise WorkbenchError('Workspace catalog exceeds size budget.',status=503,code='invalid_collection')
        data,_=read_json(path)
        if not isinstance(data,dict) or data.get('schema_version')!='workspace-collection/1' or not isinstance(data.get('entries'),list) or not 1<=len(data['entries'])<=500:raise WorkbenchError('Invalid workspace catalog.',status=503,code='invalid_collection')
        seen=set();root=(self.repository.root/'local/research').resolve()
        for item in data['entries']:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not ID.fullmatch(item['id']) or item['id'] in seen or not isinstance(item.get('title'),str) or not item['title'].strip() or len(item['title'])>200 or not isinstance(item.get('fingerprint'),str) or not SHA.fullmatch(item['fingerprint']):raise WorkbenchError('Invalid workspace entry.',status=503,code='invalid_collection')
            seen.add(item['id']);relative=item.get('directory')
            if not isinstance(relative,str) or not relative or '\\' in relative or Path(relative).is_absolute() or '..' in Path(relative).parts or ':' in relative:raise WorkbenchError('Workspace directory rejected.',status=403,code='unsafe_workspace')
            target=(root/relative).resolve()
            if not within(target,root) or target==root:raise WorkbenchError('Workspace directory escaped project.',status=403,code='unsafe_workspace')
        if data.get('default_id') not in seen:raise WorkbenchError('Workspace default is not registered.',status=503,code='invalid_collection')
        return data
    def response(self):
        data=self.entries()
        return {'schema_version':'workspace-collection/1','label':str(data.get('label','研究对象'))[:30],'default_id':data.get('default_id'),'entries':[{'id':e['id'],'title':e['title']} for e in data['entries']]}
    def resolve(self, key):
        if not isinstance(key,str) or not ID.fullmatch(key):raise WorkbenchError('Workspace ID rejected.',status=403,code='unsafe_workspace')
        data=self.entries();item=next((e for e in data['entries'] if e['id']==key),None)
        if item is None:raise WorkbenchError('Workspace is not registered.',status=404,code='workspace_not_found')
        root=(self.repository.root/'local/research').resolve();path=(root/item['directory']).resolve()
        with self.repository.lock:
            cache_key=(key,str(path),item['fingerprint'])
            if cache_key not in self.cache:
                repo=Repository(Config(self.repository.root,research_dir=path,analyses_dir=self.repository.analyses_dir,max_request_bytes=self.repository.config.max_request_bytes,max_source_preview_bytes=self.repository.config.max_source_preview_bytes))
                self.cache[cache_key]=(repo,PreviewRepository(repo))
            pair=self.cache[cache_key]
        # Re-read package bytes: a same-path replacement must never reuse trust.
        if pair[0].research()[1]!=item['fingerprint']:raise WorkbenchError('Workspace package changed.',status=409,code='stale_workspace')
        return pair
