'use strict';
const repo = 'agentkiteco/agent-toolkit-community-exs';
const $ = selector => document.querySelector(selector);
let entries = [], kind = 'all', current = null, statusTimer;
function notify(message) {
  $('#status').textContent = message;
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => { $('#status').textContent = ''; }, 4000);
}
async function copy(value) {
  try { await navigator.clipboard.writeText(value); notify('Copied to clipboard'); }
  catch { notify('Clipboard unavailable. Select the text and copy it manually.'); }
}
function command() {
  $('#install-command').textContent = `npx skills add ${repo} --skill example --agent ${$('#agent').value}`;
}
// Build the preview with DOM text nodes. Repository content is never inserted as HTML.
function inline(parent, text, source) {
  const pattern = /(`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    parent.append(document.createTextNode(text.slice(cursor, match.index)));
    if (match[0].startsWith('`')) {
      const code = document.createElement('code'); code.textContent = match[0].slice(1,-1); parent.append(code);
    } else {
      const parts = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(match[0]);
      try {
        const url = new URL(parts[2], source);
        if (!['https:', 'http:'].includes(url.protocol)) throw new Error('Unsafe link');
        const link = document.createElement('a'); link.textContent = parts[1]; link.href = url.href; parent.append(link);
      } catch { parent.append(document.createTextNode(parts[1])); }
    }
    cursor = match.index + match[0].length;
  }
  parent.append(document.createTextNode(text.slice(cursor)));
}
function markdown(body, source) {
  const fragment = document.createDocumentFragment();
  let paragraph = [], list = null, code = null;
  function flush() {
    if (paragraph.length) { const p = document.createElement('p'); inline(p,paragraph.join(' '),source); fragment.append(p); paragraph=[]; }
  }
  for (const line of body.split('\n')) {
    if (line.startsWith('```')) {
      flush(); list = null;
      if (code !== null) { const pre=document.createElement('pre'); const content=document.createElement('code'); content.textContent=code.join('\n'); pre.append(content); fragment.append(pre); code=null; }
      else code=[];
      continue;
    }
    if (code !== null) { code.push(line); continue; }
    if (!line.trim()) { flush(); list=null; continue; }
    const heading = /^(#{1,6})\s+(.+)$/.exec(line);
    if (heading) { flush(); list=null; const el=document.createElement(`h${Math.min(heading[1].length,3)}`); inline(el,heading[2],source); fragment.append(el); continue; }
    const item = /^(?:(\d+)\.\s+|[-*]\s+)(.+)$/.exec(line);
    if (item) {
      flush(); const type=item[1]?'ol':'ul';
      if (!list || list.tagName.toLowerCase() !== type) { list=document.createElement(type); fragment.append(list); }
      const li=document.createElement('li'); inline(li,item[2],source); list.append(li); continue;
    }
    list=null; paragraph.push(line);
  }
  flush();
  if (code !== null) { const pre=document.createElement('pre'); pre.textContent=code.join('\n'); fragment.append(pre); }
  return fragment;
}
function setView(view) {
  $('#detail-rendered').hidden = view !== 'preview';
  $('#detail-body').hidden = view !== 'source';
  for (const button of document.querySelectorAll('[data-view]')) button.setAttribute('aria-pressed', String(button.dataset.view === view));
}
function openEntry(entry) {
  current=entry;
  $('#detail-type').textContent = entry.kind + ' / example collection';
  $('#detail-title').textContent=entry.name;
  $('#detail-description').textContent=entry.description;
  $('#detail-body').textContent=entry.body;
  $('#detail-rendered').replaceChildren(markdown(entry.body,entry.source));
  $('#source-link').href=entry.source;
  setView('preview');
  document.body.classList.add('modal-open');
  $('#detail').showModal();
  $('#detail .detail-scroll').scrollTop=0;
}
function render() {
  const q=$('#search').value.trim().toLowerCase();
  const shown=entries.filter(e=>(kind==='all'||e.kind===kind)&&`${e.name} ${e.description} ${e.kind}`.toLowerCase().includes(q));
  $('#cards').replaceChildren();
  for (const entry of shown) {
    const card=document.createElement('article'); card.className='card';
    const top=document.createElement('div'); top.className='card-top';
    const icon=document.createElement('span'); icon.className='card-icon'; icon.setAttribute('aria-hidden','true'); icon.textContent={skill:'{ }',prompt:'>_',instruction:'≡'}[entry.kind];
    const type=document.createElement('span'); type.className='card-type'; type.textContent=entry.kind;
    top.append(icon,type);
    const title=document.createElement('h3'); title.textContent=entry.name;
    const desc=document.createElement('p'); desc.textContent=entry.description;
    const button=document.createElement('button'); button.type='button'; button.setAttribute('aria-label',`View ${entry.name} ${entry.kind}`);
    const label=document.createElement('span'); label.textContent='View '+entry.kind;
    const arrow=document.createElement('span'); arrow.textContent='↗'; arrow.setAttribute('aria-hidden','true');
    button.append(label,arrow); button.addEventListener('click',()=>openEntry(entry));
    card.append(top,title,desc,button); $('#cards').append(card);
  }
  $('#result-count').textContent=`${shown.length} ${shown.length===1?'item':'items'}`;
  $('#empty').hidden=shown.length!==0;
}
function selectKind(next) {
  kind=next;
  for (const b of document.querySelectorAll('[data-kind]')) b.setAttribute('aria-pressed',String(b.dataset.kind===kind));
  render();
}
for (const button of document.querySelectorAll('[data-kind]')) button.addEventListener('click',()=>selectKind(button.dataset.kind));
for (const button of document.querySelectorAll('[data-view]')) button.addEventListener('click',()=>setView(button.dataset.view));
$('#search').addEventListener('input',render);
$('#reset-search').addEventListener('click',()=>{ $('#search').value=''; selectKind('all'); $('#search').focus(); });
$('#agent').addEventListener('change',command);
$('#copy-command').addEventListener('click',()=>copy($('#install-command').textContent));
$('#copy-body').addEventListener('click',()=>{if(current)copy(current.body);});
$('#close-detail').addEventListener('click',()=>$('#detail').close());
$('#detail').addEventListener('close',()=>document.body.classList.remove('modal-open'));
$('#detail').addEventListener('click',event=>{
  if(event.target!==$('#detail'))return;
  const rect=event.target.getBoundingClientRect();
  if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)event.target.close();
});
command();
fetch(document.body.dataset.catalog || './catalog.json').then(response=>{
  if(!response.ok)throw new Error('Catalog request failed');
  return response.json();
}).then(data=>{entries=data;render();}).catch(()=>{
  $('#result-count').textContent='The collection could not load. Refresh the page or browse the source on GitHub.';
});
