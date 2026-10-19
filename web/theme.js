// Shared renderer: local visual inputs never become executable markup or CSS URLs.
export async function applyPresentation() {
  const status=document.getElementById('theme-status');
  try {
    const response=await fetch('/api/presentation');
    if(!response.ok)throw new Error('主题不可用');
    const theme=await response.json();
    for(const [key,value] of Object.entries(theme.palette||{}))
      if(['background','surface','text','muted','accent','line'].includes(key)&&/^#[a-f0-9]{6}$/i.test(value))document.documentElement.style.setProperty('--cl-'+key,value);
    for(const node of document.querySelectorAll('[data-theme-title]'))node.textContent=theme.status==='ready'?theme.title:node.textContent;
    for(const node of document.querySelectorAll('[data-theme-subtitle]'))node.textContent=theme.subtitle;
    if(theme.hero?.url==='/api/presentation/hero'){
      for(const node of document.querySelectorAll('[data-theme-image]')){
        node.src=theme.hero.url;node.alt=theme.hero.alt||'';
        node.addEventListener('load',()=>{node.hidden=false;document.body.classList.add('has-artwork')},{once:true});
        node.addEventListener('error',()=>{node.hidden=true;if(status)status.textContent='主视觉未载入，研究内容仍可查看。'},{once:true});
      }
      const credit=document.getElementById('art-credit');
      if(credit){credit.textContent=theme.hero.credit;credit.hidden=!theme.hero.credit;const source=theme.hero.source_url;if(typeof source==='string'&&source.startsWith('https://')){credit.href=source;credit.rel='noreferrer';credit.target='_blank'}}
    }
    if(theme.diagnostic&&status){status.textContent=theme.diagnostic;status.hidden=false}
    return theme;
  }catch(error){if(status){status.textContent='主题未载入，使用默认布局。';status.hidden=false}return {status:'unavailable'}}
}
await applyPresentation();
