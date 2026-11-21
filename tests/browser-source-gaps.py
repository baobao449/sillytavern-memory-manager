# Isolated regression for missing source tags. Uses synthetic chat data and never contacts a model.
import functools
import http.server
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent.parent
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(server.server_port)

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
 page=browser.new_page(viewport={'width':390,'height':900})
 errors=[];dialogs=[];api_calls=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('dialog',lambda d:(dialogs.append(d.message),d.dismiss()))
 page.route('**/script.js',lambda r:r.fulfill(content_type='text/javascript',body='export function isGenerating(){return false}'))
 page.route('**/scripts/world-info.js',lambda r:r.fulfill(content_type='text/javascript',body='export const world_info={};export async function loadWorldInfo(){return {entries:{}}}'))
 page.route('**/scripts/chats.js',lambda r:r.fulfill(content_type='text/javascript',body='export async function hideChatMessageRange(){}'))
 page.route('**/api/chats/get',lambda r:r.fulfill(json=[]))
 def unexpected_api(route):
  api_calls.append(route.request.url);route.fulfill(status=500,json={'error':{'message':'unexpected model request'}})
 page.route('**/api/backends/chat-completions/generate',unexpected_api)
 page.goto(url+'/package.json')
 page.evaluate("""()=>{
  document.body.innerHTML='<div id="extensionsMenu"></div>';
  const ns='st_memory_manager',chat=[
   {name:'Role',is_user:false,mes:'<think>隐藏思考</think>没有标签的开场白'},
   {name:'Role',is_user:false,mes:'没有标签的普通楼层'},
  ];
  const c={chat,chatId:'gap-test',characterId:0,characters:[{name:'Mock',avatar:'mock.png'}],name2:'Mock',
   chatMetadata:{[ns]:{schema:1,memories:[],batches:[],hidden:[],recall:{},revision:0,options:{autoStartFloor:0}}},
   extensionSettings:{[ns]:{settingsSchema:2,pluginEnabled:true,enabled:true,autoSummary:true,autoStartFloor:0,autoBatchSize:2,check:false,filterVersion:3,filterMode:'combined',sourceTag:'content',excludeTags:'think'}},
   eventTypes:{MESSAGE_RECEIVED:'received'},eventSource:{on:(name,fn)=>{window.handlers[name]=fn}},
   getRequestHeaders:()=>({'Content-Type':'application/json'}),saveMetadata:async()=>{},saveSettingsDebounced:()=>{},setExtensionPrompt:()=>{}};
  window.handlers={};window.SillyTavern={getContext:()=>c};
  localStorage.setItem(ns+':history-reminder:character:mock.png::gap-test','0:2:2');
 }""")
 page.evaluate("import('/index.js?source-gap-test')")
 page.locator('#smm-entry').wait_for()
 extracted=page.evaluate("""async()=>{
  const {sourceSnapshot}=await import('/core.js?source-gap-test');
  const c=window.SillyTavern.getContext(),s=c.extensionSettings.st_memory_manager;
  return sourceSnapshot(c.chat,0,1,s).map(({floor,text,missing})=>({floor,text,missing}));
 }""")
 assert extracted==[
  {'floor':0,'text':'没有标签的开场白','missing':False},
  {'floor':1,'text':'','missing':True},
 ],extracted
 page.evaluate("window.handlers.received()")
 page.wait_for_timeout(800)
 assert len(dialogs)==1,dialogs
 assert '第 1 层未提取到正文' in dialogs[0],dialogs
 assert api_calls==[],api_calls
 page.locator('#smm-entry').click();page.get_by_role('button',name='总结',exact=True).click()
 assert '已暂停' in page.locator('#smm-auto-status').text_content()
 assert errors==[],errors
 print('floor 0 whitelist bypass, blacklist filtering, and one-shot cancellation passed')
 browser.close()
server.shutdown()
