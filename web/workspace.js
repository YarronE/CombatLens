// Workspace identity lives in the URL, so separate tabs never share a mutable selection.
export function workspacePrefix(path=globalThis.location?.pathname||'') {
  const match=/^\/workspaces\/([A-Za-z0-9][A-Za-z0-9_-]{0,79})(?:\/|$)/.exec(path);
  return match?'/workspaces/'+match[1]:'';
}
export function apiURL(path,pathname=globalThis.location?.pathname||'') {
  if(!path.startsWith('/api/'))throw new Error('Expected local API path');
  return workspacePrefix(pathname)+path;
}
export async function mountWorkspaces(){
  for(const link of document.querySelectorAll('a[href="/"]'))link.setAttribute('href',workspacePrefix()+'/');
  for(const link of document.querySelectorAll('a[href^="/api/"]'))link.setAttribute('href',apiURL(link.getAttribute('href')));
  try {
    const response=await fetch(apiURL('/api/workspaces'),{cache:'no-store'});
    if(!response.ok)return;
    const data=await response.json();
    if(data.schema_version!=='workspace-collection/1'||!Array.isArray(data.entries)||!data.entries.length)return;
    const host=document.querySelector('.brand-bar')||document.querySelector('header');if(!host)return;
    const select=document.createElement('select');select.setAttribute('aria-label',data.label||'研究对象');select.className='workspace-picker';
    for(const item of data.entries){const option=document.createElement('option');option.value=item.id;option.textContent=item.title;select.append(option)}
    select.value=workspacePrefix().split('/')[2]||data.default_id;
    select.addEventListener('change',()=>{const tail=location.pathname.endsWith('viewer.html')?'viewer.html':location.pathname.endsWith('game.html')?'game.html':'';location.assign('/workspaces/'+encodeURIComponent(select.value)+'/'+tail)});
    host.append(select);
  }catch{/* Existing single-workspace pages remain usable offline. */}
}
if(typeof document!=='undefined')mountWorkspaces();
