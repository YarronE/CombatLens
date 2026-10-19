"""Reviewed local visual identity; never accepts arbitrary browser file paths."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT={'status':'default','title':'战斗研究工作台','subtitle':'查看动作、规则与来源','palette':{},'hero':None}
TOKENS={'background','surface','text','muted','accent','line'}

def resolve(repository):
    root=(repository.root/'local/presentations').resolve()
    try:
        report_path=repository.research_dir/'run-report.json'
        report=json.loads(report_path.read_text(encoding='utf-8')) if report_path.is_file() else {}
        adapter=report.get('adapter','') if isinstance(report,dict) else ''
        run_manifest=repository.research_dir/'presentation.json'
        path=run_manifest if run_manifest.is_file() else root/adapter/'theme.json' if re.fullmatch(r'[a-zA-Z0-9_-]+',adapter) else None
        if path is None or not path.is_file():return dict(DEFAULT),None
        # The run itself is already selected by the repository, not by a URL.
        if path!=run_manifest and not path.resolve().is_relative_to(root):raise ValueError('Presentation manifest escapes its local directory')
        if path.stat().st_size>32768:raise ValueError('Presentation manifest exceeds size limit')
        data=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or data.get('schema')!='combatlens-presentation/1':raise ValueError('Unsupported presentation schema')
        palette=data.get('palette',{})
        if not isinstance(palette,dict) or any(k not in TOKENS or not isinstance(v,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',v) for k,v in palette.items()):raise ValueError('Presentation colors must be six-digit hex tokens')
        result={'status':'ready','title':str(data.get('title',DEFAULT['title']))[:120],'subtitle':str(data.get('subtitle',DEFAULT['subtitle']))[:220],'palette':palette,'hero':None}
        asset=None;hero=data.get('hero')
        if hero:
            if not isinstance(hero,dict):raise ValueError('Invalid image registration')
            relative=Path(hero.get('path',''))
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('Image path must be relative to local/presentations')
            asset=(root/relative).resolve()
            if not asset.is_relative_to(root) or not asset.is_file():raise ValueError('Registered image is unavailable')
            if asset.stat().st_size>12*1024*1024:raise ValueError('Registered image exceeds size limit')
            raw=asset.read_bytes()
            valid=(asset.suffix.lower()=='.png' and raw.startswith(b'\x89PNG\r\n\x1a\n')) or (asset.suffix.lower() in {'.jpg','.jpeg'} and raw.startswith(b'\xff\xd8\xff'))
            if not valid:raise ValueError('Registered image must be PNG or JPEG')
            digest=hashlib.sha256(raw).hexdigest()
            if digest!=hero.get('sha256'):raise ValueError('Registered image digest changed')
            link=str(hero.get('source_url',''));parts=urlsplit(link)
            if link and (parts.scheme!='https' or not parts.netloc or parts.username or parts.password):raise ValueError('Image attribution requires an HTTPS source')
            result['hero']={'url':'/api/presentation/hero','sha256':digest,'alt':str(hero.get('alt','研究主题主视觉'))[:180],'credit':str(hero.get('credit',''))[:180],'source_url':link}
        return result,asset
    except (OSError,ValueError,TypeError,KeyError) as error:
        return dict(DEFAULT,status='unavailable',diagnostic='主题未载入；使用默认布局。'+str(error)),None
