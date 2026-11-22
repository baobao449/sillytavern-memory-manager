import {escapeHtml as h} from './core.js?v=0.7.10';

const KEY='st_memory_manager:launchers';
const DEFAULT_COLOR='#000000';
const WEBP_DATA_RE=/^data:image\/webp;base64,[a-z0-9+/=]+$/i;
const clamp=(n,min,max)=>Math.min(Math.max(n,min),max);
const unit=(n)=>Number.isFinite(n)?clamp(n,0,1):.5;
const symbol=(text)=>[...String(text||'').trim()].slice(0,4).join('');
const color=(text)=>/^#[0-9a-f]{6}$/i.test(text)?text:DEFAULT_COLOR;

function read(version){
 let saved={};
 try{saved=JSON.parse(localStorage.getItem(KEY))||{};}catch{}
 const upgraded=saved.version!==version;
 return {version,ballOn:upgraded||saved.ballOn!==false,edgeOn:saved.edgeOn===true,
  x:upgraded ? .5 : unit(saved.x),y:upgraded ? .5 : unit(saved.y),edgeY:unit(saved.edgeY),side:saved.side==='left'?'left':'right',
  text:symbol(saved.text),color:color(saved.color==='#365b7c'&&!saved.colorCustomized?'':saved.color),colorCustomized:saved.colorCustomized===true,image:typeof saved.image==='string'&&saved.image.length<100000&&WEBP_DATA_RE.test(saved.image)?saved.image:''};
}

export function launcherControls(s){
 return `<div class="smm-launcher-controls"><section>
 <input type="checkbox" data-launcher="ballOn" aria-label="启用悬浮球" ${s.ballOn?'checked':''}>
 <details><summary>悬浮球</summary><div class="smm-launcher-options">
 <button type="button" class="smm-text-button" data-launcher="ballReset">重置</button>
 <label>自定义符号或文字<input type="text" data-launcher="text" maxlength="8" value="${h(s.text)}" placeholder="留空使用默认图标"></label>
 <label>悬浮球颜色<input type="color" data-launcher="color" value="${s.color}"></label>
 <label>悬浮球图片<input type="file" data-launcher="image" accept="image/png,image/jpeg,image/webp"></label>
 <button type="button" data-launcher="imageClear" ${s.image?'':'hidden'}>移除图片</button>
 <output data-launcher-status role="status"></output>
 </div></details></section><section>
 <input type="checkbox" data-launcher="edgeOn" aria-label="启用吸附侧边栏" ${s.edgeOn?'checked':''}>
 <details><summary>吸附侧边栏</summary><div class="smm-launcher-options"><button type="button" class="smm-text-button" data-launcher="edgeReset">重置</button></div></details>
 </section></div>`;
}

async function thumbnail(file){
 if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>8*1024*1024)throw Error('请选择 8 MB 以内的 PNG、JPG 或 WebP 图片');
 const bmp=await createImageBitmap(file,{resizeWidth:128,resizeHeight:128,resizeQuality:'high'});
 try{
  const canvas=document.createElement('canvas');canvas.width=canvas.height=128;
  canvas.getContext('2d').drawImage(bmp,0,0);
  const data=canvas.toDataURL('image/webp',.85);
  if(!WEBP_DATA_RE.test(data)||data.length>=100000)throw Error('无法保存该图片');
  return data;
 }finally{bmp.close();}
}

export function installLaunchers(version,open){
 const state=read(version);
 const persist=()=>{try{localStorage.setItem(KEY,JSON.stringify(state));return true;}catch{return false;}};
 function mount(kind,label){
  const el=document.createElement('div');el.className=`smm-launcher smm-launcher-${kind}`;
  el.innerHTML=`<button type="button" class="smm-launcher-open" aria-label="${label}打开记忆管理器" title="打开记忆管理器"></button>`;
  document.body.append(el);
  return {el,button:el.firstElementChild};
 }
 const ball=mount('ball','悬浮球'),edge=mount('edge','侧边栏');
 function setIcon(target,icon){const i=document.createElement('i');i.className=`fa-solid ${icon}`;i.setAttribute('aria-hidden','true');target.replaceChildren(i);}
 function appearance(){
  ball.button.style.backgroundColor=state.color;
  const rgb=state.color.slice(1).match(/../g).map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);
  ball.button.style.color=(rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722)>.179?'#111':'#fff';
  if(state.image){const img=document.createElement('img');img.src=state.image;img.alt='';ball.button.replaceChildren(img);}
  else if(state.text)ball.button.textContent=state.text;
  else setIcon(ball.button,'fa-layer-group');
 }
 const extent=()=>({w:document.documentElement.clientWidth||innerWidth,h:innerHeight});
 const bounds=(value,size,margin)=>clamp(value,Math.min(margin,size/2),Math.max(size-margin,size/2));
 function placeBall(x,y){const {w,h}=extent();ball.el.style.left=`${bounds(x,w,27)}px`;ball.el.style.top=`${bounds(y,h,27)}px`;}
 function placeEdge(x,y,side){const {h}=extent();edge.el.dataset.side=side;edge.el.style.left=`${x}px`;edge.el.style.top=`${bounds(y,h,43)}px`;}
 function layout(){const {w,h}=extent();placeBall(state.x*w,state.y*h);placeEdge(state.side==='left'?0:w,state.edgeY*h,state.side);}
 function visible(){
  ball.el.hidden=!state.ballOn;edge.el.hidden=!state.edgeOn;
  for(const key of ['ballOn','edgeOn']){const input=document.querySelector(`#smm-panel [data-launcher=${key}]`);if(input)input.checked=state[key];}
 }
 function toggle(key,value){state[key]=value;visible();persist();}
 // An inward swipe can suppress Chromium's next synthesized click. Handle a deliberate tap on the panel close button directly.
 let closeTap;
 document.addEventListener('touchstart',e=>{
  const button=e.target.closest('#smm-panel > header [data-action=close]'),touch=e.changedTouches[0];
  closeTap=button&&e.touches.length===1?{button,id:touch.identifier,x:touch.clientX,y:touch.clientY}:null;
 },{passive:true});
 document.addEventListener('touchcancel',()=>{closeTap=null;},{passive:true});
 document.addEventListener('touchend',e=>{
  const tap=closeTap;closeTap=null;
  if(!tap)return;
  const touch=Array.from(e.changedTouches).find(t=>t.identifier===tap.id);
  if(!touch||Math.hypot(touch.clientX-tap.x,touch.clientY-tap.y)>8||!tap.button.contains(document.elementFromPoint(touch.clientX,touch.clientY)))return;
  e.preventDefault();tap.button.click();
 },{passive:false});
 function drag(target,isEdge){
  let gesture=null,suppressClick=false;
  const {el,button}=target;
  button.addEventListener('pointerdown',e=>{
   if(gesture||e.button!==0||!e.isPrimary)return;
   suppressClick=false;gesture={id:e.pointerId,x:e.clientX,y:e.clientY,top:parseFloat(el.style.top),left:parseFloat(el.style.left),side:state.side,moved:false};
   button.setPointerCapture(e.pointerId);
  });
  function move(e){
   if(gesture?.id!==e.pointerId)return;
   const dx=e.clientX-gesture.x,dy=e.clientY-gesture.y;
   if(!gesture.moved&&Math.hypot(dx,dy)<7)return;
   gesture.moved=true;el.classList.add('smm-launcher-moving');
   const {w}=extent();
   if(isEdge)placeEdge(clamp(gesture.left+dx,0,w),gesture.top+dy,gesture.side);
   else placeBall(gesture.left+dx,gesture.top+dy);
  }
  function finish(e,cancelled){
   if(gesture?.id!==e.pointerId)return;
   if(!cancelled)move(e);
   const g=gesture;gesture=null;el.classList.remove('smm-launcher-moving');
   if(g.moved){
    suppressClick=true;
    if(!cancelled){
     const {w,h}=extent();
     if(isEdge){
      const x=parseFloat(el.style.left),inward=(e.clientX-g.x)*(g.side==='left'?1:-1);
      state.side=x<w/2?'left':'right';state.edgeY=unit(parseFloat(el.style.top)/h);
      if(state.side===g.side&&inward>=30&&inward>Math.abs(e.clientY-g.y))requestAnimationFrame(()=>{if(state.edgeOn)open();});
     }else{state.x=unit(parseFloat(el.style.left)/w);state.y=unit(parseFloat(el.style.top)/h);}
     persist();
    }
    layout();
   }
  }
  button.addEventListener('pointermove',move);
  button.addEventListener('pointerup',e=>finish(e,false));
  for(const type of ['pointercancel','lostpointercapture'])button.addEventListener(type,e=>finish(e,true));
  button.addEventListener('click',e=>{if(e.detail===0||!suppressClick)open();suppressClick=false;});
 }
 drag(ball,false);drag(edge,true);setIcon(edge.button,'fa-layer-group');
 let imageRequest=0;
 function updateImage(data){
  const previous=state.image;state.image=data;
  if(!persist()){state.image=previous;throw Error('浏览器没有足够空间保存这张图片');}
  appearance();
  const remove=document.querySelector('#smm-panel [data-launcher=imageClear]');if(remove)remove.hidden=!data;
 }
 function status(message){const output=document.querySelector('#smm-panel [data-launcher-status]');if(output)output.textContent=message;}
 document.addEventListener('change',async e=>{
  const input=e.target,key=input.closest('#smm-panel')&&input.dataset.launcher;
  if(key==='ballOn'||key==='edgeOn'){toggle(key,input.checked);return;}
  if(key==='text'||key==='color'){
   state[key]=key==='text'?symbol(input.value):color(input.value);if(key==='color')state.colorCustomized=true;input.value=state[key];appearance();persist();
  }else if(key==='image'&&input.files[0]){
   const request=++imageRequest,file=input.files[0];input.value='';
   try{const data=await thumbnail(file);if(request===imageRequest){updateImage(data);status('图片已保存');}}
   catch(error){if(request===imageRequest)status(error.message||'图片无法读取');}
  }
 });
 document.addEventListener('click',e=>{
  const key=e.target.closest('#smm-panel button[data-launcher]')?.dataset.launcher;
  if(key==='ballReset'){state.x=state.y=.5;layout();persist();}
  if(key==='edgeReset'){state.side='right';state.edgeY=.5;layout();persist();}
  if(key==='imageClear'){imageRequest++;try{updateImage('');status('图片已移除');}catch(error){status(error.message);}}
 });
 window.addEventListener('resize',layout);
 appearance();layout();visible();persist();
 return ()=>launcherControls(state);
}
