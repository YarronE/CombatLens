"""CLI used by agents and people. Viewing prepared research needs no API key."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen
from .orchestrator import ROOT,analyze,configured,demo,load_json,save_json
from .runtime.repository import Config
from .runtime.server import WorkbenchServer,Handler
from .runtime.repository import Repository

class LensHandler(Handler):
    pass

def active(root=ROOT):
    config=Config(root);return config.paths()[1]

def serve(research,port,ready=None):
    server=WorkbenchServer(('127.0.0.1',port),Repository(Config(ROOT,research_dir=research)))
    server.RequestHandlerClass=LensHandler
    status={'pid':os.getpid(),'port':server.server_port,'url':'http://127.0.0.1:'+str(server.server_port)+'/','run_id':load_json(research/'run-report.json')['id'],'workspace_fingerprint':hashlib.sha256(ROOT.resolve().as_posix().lower().encode()).hexdigest()}
    if ready:save_json(ready,status)
    print(json.dumps(status),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

def start(research,port=8877):
    expected=load_json(research/'run-report.json')['id']
    recorded=research/'service.json'
    if recorded.is_file():
        try:
            saved=load_json(recorded);saved_port=saved.get('port')
            if type(saved_port) is int and 1<=saved_port<=65535:
                base='http://127.0.0.1:'+str(saved_port)
                with urlopen(base+'/api/health',timeout=.5) as response:health=json.load(response)
                with urlopen(base+'/api/run',timeout=.5) as response:report=json.load(response)
                fp=hashlib.sha256(ROOT.resolve().as_posix().lower().encode()).hexdigest()
                if health.get('service')=='combatlens' and health.get('workspace_fingerprint')==fp and report.get('id')==expected:
                    return {'status':'reused','url':base+'/','pid':health['pid']}
        except Exception:pass
    for selected in range(port,port+20):
        base='http://127.0.0.1:'+str(selected)
        try:
            with urlopen(base+'/api/health',timeout=.4) as response:health=json.load(response)
            with urlopen(base+'/api/run',timeout=.4) as response:report=json.load(response)
            fp=hashlib.sha256(ROOT.resolve().as_posix().lower().encode()).hexdigest()
            if health.get('service')=='combatlens' and health.get('workspace_fingerprint')==fp and report.get('id')==expected:return {'status':'reused','url':base+'/','pid':health['pid']}
            continue
        except Exception:pass
        ready=research/'service.json';logs=ROOT/'local/logs';logs.mkdir(parents=True,exist_ok=True)
        stdout=(logs/(expected+'-'+str(selected)+'.out.log')).open('ab');stderr=(logs/(expected+'-'+str(selected)+'.err.log')).open('ab')
        command=[sys.executable,str(ROOT/'run.py'),'serve','--research',str(research),'--port',str(selected),'--ready',str(ready)]
        flags=subprocess.CREATE_NO_WINDOW|subprocess.DETACHED_PROCESS if os.name=='nt' else 0
        child=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,creationflags=flags,start_new_session=os.name!='nt');stdout.close();stderr.close()
        for _ in range(60):
            if child.poll() is not None:break
            if ready.exists():
                state=load_json(ready)
                if state.get('pid')==child.pid:
                    try:
                        with urlopen(state['url']+'api/run',timeout=.5) as response:report=json.load(response)
                        if report.get('id')==expected:return {'status':'started',**state}
                    except Exception:pass
            time.sleep(.1)
        # Clean up only the child this start attempt owns.
        if child.poll() is None:child.terminate();child.wait(timeout=5)
    raise ValueError('No available matching loopback service; inspect local/logs')

def main(argv=None):
    parser=argparse.ArgumentParser(prog='combatlens',description='Agent-driven combat research workspace')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor');sub.add_parser('adapters')
    reg=sub.add_parser('register');reg.add_argument('manifest',type=Path)
    task=sub.add_parser('analyze');task.add_argument('request');task.add_argument('--adapter');task.add_argument('--open',action='store_true');task.add_argument('--port',type=int,default=8877)
    show=sub.add_parser('demo');show.add_argument('--open',action='store_true');show.add_argument('--port',type=int,default=8877)
    running=sub.add_parser('serve');running.add_argument('--research',type=Path);running.add_argument('--port',type=int,default=8877);running.add_argument('--ready',type=Path)
    sub.add_parser('start')
    snapshot=sub.add_parser('freeze');snapshot.add_argument('destination',type=Path);snapshot.add_argument('--research',type=Path);snapshot.add_argument('--attachment',type=Path,action='append',default=[])
    args=parser.parse_args(argv)
    try:
        if args.command=='doctor':result={'python':sys.version.split()[0],'rea_cli':shutil.which('rea'),'adapters':[{'id':item['id'],'entrypoint_present':Path(item['entrypoint']).is_file(),'capabilities':item.get('capabilities',[])} for item in configured()['adapters']],'note':'REA MCP availability is checked by the agent; a missing CLI does not prove the MCP is unavailable.'}
        elif args.command=='adapters':result={'adapters':[{k:item.get(k) for k in ['id','name','aliases','capabilities']} for item in configured()['adapters']]}
        elif args.command=='register':
            manifest=load_json(args.manifest)
            if not all(isinstance(manifest.get(k),str) and manifest[k] for k in ['id','entrypoint']) or not isinstance(manifest.get('aliases'),list) or not all(isinstance(x,str) and x for x in manifest['aliases']):raise ValueError('Invalid adapter manifest')
            manifest['entrypoint']=str((args.manifest.resolve().parent/manifest['entrypoint']).resolve())
            if not Path(manifest['entrypoint']).is_file():raise ValueError('Missing reviewed adapter entrypoint')
            registry=configured();registry['adapters']=[item for item in registry['adapters'] if item['id']!=manifest['id']]+[manifest];save_json(ROOT/'local/config.json',registry);result={'registered':manifest['id']}
        elif args.command in ['demo','analyze']:
            result=demo() if args.command=='demo' else analyze(args.request,adapter_id=args.adapter)
            if args.open:result['service']=start(Path(result['research_dir']),args.port)
        elif args.command=='freeze':
            from .bundle import freeze
            result=freeze(ROOT,args.research or active(),args.destination,args.attachment)
        elif args.command=='start':result=start(active())
        else:serve(args.research or active(),args.port,args.ready);return 0
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False));return 0
    except Exception as error:print(json.dumps({'error':type(error).__name__,'message':str(error)},ensure_ascii=False),file=sys.stderr);return 1
