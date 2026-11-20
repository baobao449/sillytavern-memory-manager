# Isolated browser regression: all chat content and network responses below are synthetic fixtures.
# Run with Python Playwright and Microsoft Edge installed. No real account/API is contacted.
import json,threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent
(root/'output').mkdir(exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(server.server_port)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
 results=[]
 for width in [390,1280]:
  page=browser.new_page(viewport={'width':width,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('dialog',lambda d:d.accept());page.goto(url+'/package.json')
  page.evaluate("""()=>{document.body.innerHTML='<div id="extensionsMenu"></div>';const l=document.createElement('link');l.rel='stylesheet';l.href='/style.css';document.head.append(l);const ns='st_memory_manager';const c={chat:Array.from({length:30},(_,i)=>({name:i%2?'Role':'User',is_user:i%2===0,mes:i%2?'<CONTENT>真实原话。阿宁持有铜印。':'你好'})),chatId:'flow-test',characterId:0,characters:[{name:'Mock',avatar:'mock.png',data:{extensions:{world:'Test Book'}}}],name2:'Mock',chatMetadata:{[ns]:{schema:1,memories:[],batches:[],hidden:[],recall:{},revision:0,options:{baseUrl:'bad-old',filterVersion:1,batchSize:0}}},extensionSettings:{[ns]:{baseUrl:'https://old.invalid',customCss:'bad-old-css',attics:{'mock.png':{memories:[]}}}},eventTypes:{CHAT_CHANGED:'CHAT_CHANGED',MESSAGE_RECEIVED:'received',GENERATION_AFTER_COMMANDS:'inject',CHAT_COMPLETION_PROMPT_READY:'ready'},eventSource:{on:(name,fn)=>{window.handlers[name]=fn}},getRequestHeaders:()=>({'Content-Type':'application/json'}),saveMetadata:async()=>{window.savedStore=structuredClone(c.chatMetadata)},saveSettingsDebounced:()=>{},setExtensionPrompt:(_id,text)=>window.injected=text};window.handlers={};window.SillyTavern={getContext:()=>c};}""")
  page.route('**/script.js',lambda r:r.fulfill(content_type='text/javascript',body='export function isGenerating(){return false}'))
  page.route('**/scripts/world-info.js',lambda r:r.fulfill(content_type='text/javascript',body='export const world_info={};export async function loadWorldInfo(){return {entries:{0:{uid:0,content:"WORLD_EVIDENCE 有效世界书内容",key:["铜印"],disable:false}}}}'))
  page.route('**/scripts/chats.js',lambda r:r.fulfill(content_type='text/javascript',body='export async function hideChatMessageRange(start,end){for(let i=start;i<=end;i++)window.SillyTavern.getContext().chat[i].is_system=true}'))
  page.route('**/api/chats/get',lambda r:r.fulfill(json=[{'chat_metadata':page.evaluate('window.savedStore')}]))
  behavior={'drift':False,'fail':False,'multi':False};repair_calls=[];calls={'summary':0,'check':0};check_sizes=[];revisions=[];theme_checks=[];held=[];hold={'value':False}
  def generate(route):
   data=route.request.post_data_json;payload=json.loads(data['messages'][-1]['content'])
   if 'revision' in payload.get('task',{}):revisions.append(payload['task']['revision'])
   if 'items' in payload:
    content=json.dumps({'items':[{'id':m['id'],'keywords':['铜印','阿宁']} for m in payload['items']]},ensure_ascii=False)
   elif 'originalResponse' in payload:
    repair_calls.append(data);content=json.dumps({'memories':[{'summary':'修复后的有效记忆','sources':list(range(10))}]},ensure_ascii=False)
   elif 'draft' in payload:
    calls['check']+=1;check_sizes.append(len(payload['draft']));content=json.dumps({'issues':[{'id':payload['draft'][0]['id'],'message':'核对时间','suggestion':'不要推断日期','quote':'阿宁持有铜印','field':'summary'}]},ensure_ascii=False)
   else:
    calls['summary']+=1;floors=[s['floor'] for s in payload['sources']];content=json.dumps({'memories':[{'title':'测试记忆'+str(calls['summary']),'summary':'阿宁持有铜印，等待赴约。','sources':floors,'brief':'等待赴约','keywords':['铜印','赴约'],'suggestedKind':'long','details':{'quotes':['真实原话。'],'characters':'阿宁：本次持有铜印的人。'}}]},ensure_ascii=False)
   if behavior.get('checkFail') and 'draft' in payload:
    route.fulfill(json={'error':{'message':'模拟检查线路失败','code':'check_unavailable'}});return
   if behavior.get('status') and 'sources' in payload:
    parsed=json.loads(content);parsed['memories'][0]['statusUpdates']=[{'memoryId':'old','field':'promises','itemText':'阿宁归还铜印','sourceFloor':21,'evidence':'阿宁已经归还铜印，约定已完成。'}];content=json.dumps(parsed,ensure_ascii=False)
   if behavior['multi'] and 'sources' in payload and payload['sources'][0]['role']!='memory':
    parsed=json.loads(content);parsed['memories'].extend([{**parsed['memories'][0],'title':'额外测试记忆'+str(i)} for i in range(4)]);content=json.dumps(parsed,ensure_ascii=False)
   if behavior['fail'] and 'sources' in payload:
    route.abort('failed');return
   if behavior['drift'] and 'sources' in payload:content='# 角色卡\n普通 Markdown 角色信息，不是所选输出格式'
   response={'choices':[{'message':{'content':content},'finish_reason':'stop'}]};held.append((route,response)) if hold['value'] or calls['summary']>=hold.get('after',100000) else route.fulfill(json=response)
  page.route('**/api/backends/chat-completions/generate',generate)
  page.route('**/api/backends/chat-completions/status',lambda r:r.fulfill(json={'data':[{'id':'mock-model'}]}))
  page.evaluate("import('/index.js')");page.locator('#smm-entry').click()
  page.wait_for_timeout(650)
  if page.locator('[data-choice=later]').count():page.locator('[data-choice=later]').click()
  def drawers():page.evaluate("document.querySelectorAll('#smm-panel details').forEach(d=>d.open=true)")
  page.get_by_role('button',name='设置',exact=True).click();drawers()
  assert page.locator('[data-action=configuration-clean]').count()==0
  assert page.locator('#smm-entry .fa-layer-group').count()==1
  assert page.locator('[data-setting=autoSummary]').is_checked()
  assert page.locator('[data-setting=check]').is_checked()
  assert page.locator('[data-setting=promptVariant]').input_value()=='extended'
  assert page.locator('[data-setting=themePreset]').input_value()=='tavern'
  assert page.locator('[data-mode=quotes]').input_value()=='off'

  assert page.locator('[data-mode=characters]').input_value()=='separate'
  # Example is a closed disclosure even inside an expanded parent drawer.
  example=page.locator('[data-output-example]');example.locator('xpath=ancestor::details[1]').evaluate('(e)=>e.open=false')
  assert not example.is_visible()
  example.locator('xpath=ancestor::details[1]').locator('summary').click()
  page.locator('[data-setting=outputMode]').select_option('tags')
  assert '<stm4-characters>' in example.inner_text()
  page.locator('[data-mode=characters]').select_option('off')
  assert '<stm4-characters>' not in example.inner_text()
  page.locator('[data-mode=characters]').select_option('separate')
  page.locator('[data-setting=outputMode]').select_option('plain')
  assert '人物：' in example.inner_text()
  page.locator('[data-setting=outputMode]').select_option('json')
  assert 'characters' in example.inner_text()
  example.scroll_into_view_if_needed();page.screenshot(path=str(root/'output'/f'v074-output-characters-{width}.png'))
  page.locator('[data-mode=characters]').scroll_into_view_if_needed();page.screenshot(path=str(root/'output'/f'v074-characters-{width}.png'))

  # Built-in archive restores requested options without touching API credentials.
  page.locator('[data-setting=baseUrl]').fill('https://example.invalid/v1');page.locator('[data-setting=model]').fill('mock-model');page.locator('#smm-key').fill('fake-test-only')
  page.get_by_role('button',name='保存设置',exact=True).click();drawers()
  page.locator('#smm-profiles').select_option('smm-builtin-default-v057');page.wait_for_function('document.querySelector("#smm-profiles").value==="smm-builtin-default-v057"');drawers()
  assert page.locator('[data-setting=baseUrl]').input_value()=='https://example.invalid/v1'
  assert page.locator('#smm-key').input_value()=='fake-test-only'
  page.locator('[data-setting=autoSummary]').uncheck();page.locator('[data-setting=autoSecondary]').uncheck();page.locator('[data-setting=autoTertiary]').uncheck();page.locator('[data-setting=check]').uncheck();page.locator('[data-setting=autoHide]').uncheck()
  page.get_by_role('button',name='保存设置',exact=True).click()
  # Tutorial groups settings first, remains centered, and never calls a model.
  page.locator('header [data-action=tour]').click();page.locator('#smm-tour h3').wait_for();before=calls.copy()
  for step in range(1,14):
   page.wait_for_function('(n)=>document.querySelector("#smm-tour h3")?.textContent.startsWith(n+"/13")',arg=step)
   rect=page.locator('#smm-tour').bounding_box();assert abs(rect['y']+rect['height']/2-450)<3,rect
   if step<=6:assert page.locator('[data-setting=baseUrl]').count()==1
   if step==7:assert page.locator('#smm-start').count()==1
   page.locator('#smm-tour').get_by_role('button',name='完成' if step==13 else '下一步',exact=True).click()
  assert calls==before
  # Drag stays in place across steps; new tour centers again.
  page.locator('header [data-action=tour]').click();page.locator('#smm-tour h3').wait_for()
  rect=page.locator('#smm-tour').bounding_box();handle=page.locator('#smm-tour header').bounding_box()
  page.mouse.move(handle['x']+40,handle['y']+10);page.mouse.down();page.mouse.move(handle['x']+65,handle['y']+45);page.mouse.up()
  moved=page.locator('#smm-tour').bounding_box();assert abs(moved['y']-rect['y'])>10,(rect,moved)
  page.locator('#smm-tour').get_by_role('button',name='下一步',exact=True).click()
  assert abs(page.locator('#smm-tour').bounding_box()['y']-moved['y'])<3
  page.locator('#smm-tour').get_by_role('button',name='跳过',exact=True).click()
  # World books persist through unrelated settings save, request contains actual entries.
  page.route('**/scripts/world-info.js',lambda r:r.fulfill(content_type='text/javascript',body='export const world_info={};export async function loadWorldInfo(){return {entries:{0:{uid:0,content:"WORLD_EVIDENCE 有效世界书内容",key:["铜印"],disable:false}}}}'))
  # Force fresh world module: imported earlier only if references were generated.
  page.evaluate('window.SillyTavern.getContext().characters[0].data={extensions:{world:"Test Book"}}')
  page.get_by_role('button',name='总结',exact=True).click();drawers();page.locator('[data-action=books]').click();page.locator('[data-book="Test Book"]').check()
  page.get_by_role('button',name='设置',exact=True).click();drawers();page.locator('[data-action=settings-save]').click()
  assert page.evaluate('window.SillyTavern.getContext().extensionSettings.st_memory_manager.booksByCharacter["mock.png"]')==['Test Book']
  assert page.locator('.smm-settings-profiles').evaluate('(e)=>e.previousElementSibling.classList.contains("smm-plugin-control")')
  assert page.locator('.smm-migration-notice').count()==0
  assert page.locator('[data-setting=excludeTags]').input_value()=='think,thinking,details,summary'
  for tag in ['bbi_image','image','###']:assert page.locator('[data-tag-preset=excludeTags][data-tag="'+tag+'"]').count()==1
  page.locator('[data-setting=themePreset]').select_option('paper')
  assert page.locator('[data-action=settings-open]').evaluate('(e)=>getComputedStyle(e).borderTopStyle')=='none'
  assert page.locator('[data-setting=themePreset]').evaluate('(e)=>getComputedStyle(e).color')=='rgb(51, 47, 43)'
  page.get_by_role('button',name='总结',exact=True).click();drawers();page.locator('[data-action=usage-preview]').click()
  page.wait_for_function('document.querySelector("#smm-request-usage").innerText.includes("合计")')
  page.locator('#smm-prompt-preview details').evaluate_all('(ds)=>ds.forEach(d=>d.open=true)');page.wait_for_function('document.querySelector("#smm-prompt-preview").textContent.includes("WORLD_EVIDENCE")')
  assert 'WORLD_EVIDENCE' in page.locator('#smm-prompt-preview').text_content(), page.locator('#smm-prompt-preview').text_content()
  assert '世界书0 字符' not in page.locator('#smm-request-usage').inner_text()
  # Two batches generate without saving the first. Both survive a chat reload.
  page.get_by_role('button',name='总结',exact=True).click();drawers();page.locator('#smm-batch-start').fill('0');page.locator('#smm-batch-end').fill('9');page.locator('[data-setting=batchSize]').fill('5');page.locator('[data-setting=batchClassification]').select_option('manual');page.locator('#smm-batch-hide').uncheck()
  page.get_by_role('button',name='开始批量总结',exact=True).click()
  page.locator('[data-action=approve-all]').wait_for();page.wait_for_function('document.querySelector("#smm-floating-progress")?.hidden===true')
  assert calls['summary']==2,calls
  assert page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length')==0
  assert page.locator('.smm-batch-report').count()==0
  assert '2份' in page.locator('#smm-panel .smm-body').inner_text()
  captured=page.evaluate('({metadata:window.SillyTavern.getContext().chatMetadata,settings:window.SillyTavern.getContext().extensionSettings})');page.reload()
  page.evaluate("""()=>{document.body.innerHTML='<div id="extensionsMenu"></div>';const l=document.createElement('link');l.rel='stylesheet';l.href='/style.css';document.head.append(l);const ns='st_memory_manager';const c={chat:Array.from({length:30},(_,i)=>({name:i%2?'Role':'User',is_user:i%2===0,mes:i%2?'<CONTENT>真实原话。阿宁持有铜印。':'你好'})),chatId:'flow-test',characterId:0,characters:[{name:'Mock',avatar:'mock.png',data:{extensions:{world:'Test Book'}}}],name2:'Mock',chatMetadata:{[ns]:{schema:1,memories:[],batches:[],hidden:[],recall:{},revision:0,options:{baseUrl:'bad-old',filterVersion:1,batchSize:0}}},extensionSettings:{[ns]:{baseUrl:'https://old.invalid',customCss:'bad-old-css',attics:{'mock.png':{memories:[]}}}},eventTypes:{CHAT_CHANGED:'CHAT_CHANGED',MESSAGE_RECEIVED:'received',GENERATION_AFTER_COMMANDS:'inject',CHAT_COMPLETION_PROMPT_READY:'ready'},eventSource:{on:(name,fn)=>{window.handlers[name]=fn}},getRequestHeaders:()=>({'Content-Type':'application/json'}),saveMetadata:async()=>{window.savedStore=structuredClone(c.chatMetadata)},saveSettingsDebounced:()=>{},setExtensionPrompt:(_id,text)=>window.injected=text};window.handlers={};window.SillyTavern={getContext:()=>c};}""")
  page.evaluate('(saved)=>{const c=window.SillyTavern.getContext();c.chatMetadata=saved.metadata;c.extensionSettings=saved.settings}',captured)
  page.evaluate("import('/index.js')");page.locator('#smm-entry').click();page.get_by_role('button',name='待确认',exact=True).click();page.locator('[data-action=approve-all]').wait_for()
  # Confirm stays pinned while the memory body scrolls.
  for pos in [0,99999]:
   page.locator('#smm-panel .smm-body').evaluate('(e,n)=>e.scrollTop=n',pos)
   b=page.locator('.smm-save [data-action=approve]').bounding_box();r=page.locator('#smm-panel').bounding_box();assert b['y']+b['height']<=r['y']+r['height'] and b['y']>=r['y']
  page.locator('[data-action=pending-select]').click();page.locator('[data-action=approve-all]').click()
  page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===2')
  page.wait_for_function('!document.querySelector("[data-action=approve-all]")')
  assert page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.every(m=>m.details.characters==="阿宁：本次持有铜印的人。")')
  page.get_by_role('button',name='记忆',exact=True).click();drawers()
  assert page.locator('.smm-card').first.locator('h4').filter(has_text='人物').count()==1
  assert '阿宁：本次持有铜印的人。' in page.locator('.smm-card').first.inner_text()

  assert page.locator('#smm-floating-progress').is_hidden()
  page.get_by_role('button',name='总结',exact=True).click();assert page.locator('#smm-start').input_value()=='10';assert page.locator('#smm-batch-start').input_value()=='10';assert '第10-' in page.locator('#smm-auto-status').text_content()
  # Legacy stale automatic cursor ignores old holes; ignore merges the progress ranges.
  page.evaluate("""()=>{const s=window.SillyTavern.getContext().chatMetadata.st_memory_manager;s.batches=[{level:1,approved:true,floors:[1,2,3,4,6,7,8,9],selectedFloors:[0,1,2,3,4,5,6,7,8,9],ids:[]}];s.options.autoStartFloor=0;window.handlers.CHAT_CHANGED();}""")
  page.get_by_role('button',name='总结',exact=True).click();assert '第10-' in page.locator('#smm-auto-status').text_content()
  page.locator('[data-action=ignore-floors]').click();assert page.locator('dialog textarea').input_value()=='0,5';page.locator('dialog').get_by_role('button',name='确定',exact=True).click();page.locator('[data-action=ignore-reset]').wait_for()
  assert page.evaluate('JSON.stringify(window.SillyTavern.getContext().chatMetadata.st_memory_manager.ignoredFloors)')=='[0,5]'
  assert '已保存总结：第0-9楼' in page.locator('.smm-progress-board').first.inner_text()
  assert page.evaluate('window.SillyTavern.getContext().chat.filter(m=>m.is_system).length')==0
  page.locator('[data-action=ignore-reset]').click();page.wait_for_function('!document.querySelector("[data-action=ignore-reset]")')
  page.locator('[data-count-mode]').select_option('time');assert page.locator('[data-count-mode]').input_value()=='time'
  # Failed batch pauses; retry continues all remaining batches into independent drafts.
  drawers();page.locator('#smm-batch-start').fill('10');page.locator('#smm-batch-end').fill('19');page.locator('[data-setting=batchSize]').fill('5');behavior['fail']=True
  before=calls['summary'];page.get_by_role('button',name='开始批量总结',exact=True).click();page.get_by_role('button',name='重试失败批',exact=True).wait_for();assert calls['summary']==before+1
  behavior['fail']=False;page.get_by_role('button',name='重试失败批',exact=True).click();page.locator('[data-action=approve-all]').wait_for();assert calls['summary']==before+3
  assert page.locator('#smm-floating-progress').is_hidden()
  page.locator('[data-action=approve-all]').click();page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===4')
  # Save batch one while the second model response is still in flight.
  page.get_by_role('button',name='总结',exact=True).click();drawers();page.locator('#smm-batch-start').fill('20');page.locator('#smm-batch-end').fill('29');page.locator('[data-setting=batchSize]').fill('5');hold['after']=calls['summary']+2
  page.get_by_role('button',name='开始批量总结',exact=True).click()
  for _ in range(100):
   if held:break
   page.wait_for_timeout(50)
  assert len(held)==1
  page.locator('.smm-save [data-action=approve]').click();page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===5')
  del hold['after'];route,response=held.pop();route.fulfill(json=response)
  page.locator('.smm-save [data-action=approve]').wait_for();page.wait_for_function('document.querySelector("#smm-floating-progress")?.hidden===true');page.locator('.smm-save [data-action=approve]').click();page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===6')
  page.get_by_role('button',name='设置',exact=True).click();drawers();page.locator('[data-setting=fontPreset]').select_option('tavern');page.locator('[data-setting=themePreset]').select_option('tavern')
  assert page.locator('#smm-panel').evaluate('e=>!getComputedStyle(e).backgroundColor.includes("rgba")')
  # Feature UI verification on the same fully exercised isolated chat.
  assert page.locator('[data-setting=outputTokens]').count()==1
  assert page.locator('[data-setting=earlyDraft]').is_checked()==False
  page.locator('[data-setting=outputTokens]').fill('2048');page.locator('[data-setting=earlyDraft]').check();page.locator('[data-setting=check]').check()
  page.locator('[data-setting=autoSummary]').uncheck();page.locator('[data-setting=autoSecondary]').uncheck();page.locator('[data-setting=autoTertiary]').uncheck()
  page.locator('[data-action=settings-save]').click()
  page.locator('[data-tab=memories]').click();page.locator('[data-source-sort]').select_option('desc')
  page.locator('[data-action=rehearsal]').click();page.locator('.smm-rehearsal [data-start]').fill('1');page.locator('.smm-rehearsal [data-end]').fill('3');page.locator('.smm-rehearsal [data-run]').click()
  assert '最终记忆文本' in page.locator('.smm-rehearsal [data-results]').inner_text();page.locator('.smm-rehearsal [data-close]').click()
  page.evaluate('(()=>{const ms=window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories;if(!ms.some(m=>m.kind==="long")&&ms.length)ms[0].kind="long"})()');page.locator('[data-action=keyword-health]').click();assert page.locator('.smm-keywords [data-health]').count()>0;page.locator('.smm-keywords [data-generate]').click();page.locator('.smm-keywords > footer [data-cancel]').click()
  page.locator('[data-tab=summary]').click();drawers();page.locator('#smm-start').fill('0');page.locator('#smm-end').fill('3');hold['value']=True
  page.locator('[data-action=summarize]').click()
  for _ in range(100):
   if held:break
   page.wait_for_timeout(30)
  route,response=held.pop();assert route.request.post_data_json['max_tokens']==2048;route.fulfill(json=response)
  for _ in range(100):
   if held:break
   page.wait_for_timeout(30)
  assert page.locator('[data-tab=draft]').get_attribute('class')=='active'
  assert page.locator('.smm-save [data-action=approve]').is_disabled()
  assert '检查中' in page.locator('.smm-save-preview').inner_text()
  route,response=held.pop();route.fulfill(json=response);hold['value']=False
  page.wait_for_function('document.querySelector(".smm-save [data-action=approve]")?.disabled===false')
  assert page.locator('.smm-review-mark').count()>0
  assert '本次保存' in page.locator('.smm-save-preview').inner_text()
  before=calls.copy()
  page.locator('[data-action=regenerate]').click();page.locator('[data-choice=review]').click()
  page.locator('dialog').get_by_role('button',name='取消',exact=True).click()
  assert calls==before
  page.locator('[data-action=regenerate]').click();page.locator('[data-choice=review]').click()
  page.locator('dialog textarea').fill('保留这场对峙为一条记忆')
  page.locator('dialog').get_by_role('button',name='开始生成',exact=True).click()

  page.wait_for_function('!!document.querySelector("[data-action=version-select]")')
  assert '草稿差异对照' not in page.locator('.smm-body').inner_text()
  assert calls['summary']==before['summary']+1 and calls['check']==before['check']
  assert revisions[-1]['userInstruction']=='保留这场对峙为一条记忆' and revisions[-1]['reviewNotes'][0]['suggestion']=='不要推断日期'
  page.locator('[data-action=regenerate]').click();page.locator('[data-choice=review]').click()
  behavior['fail']=True
  page.locator('dialog').get_by_role('button',name='开始生成',exact=True).click()
  page.wait_for_function('document.querySelector("#smm-floating-progress")?.hidden===true')
  page.wait_for_function('document.getElementById("st_memory_manager-toast")?.textContent.includes("Failed to fetch")')
  assert calls['summary']==before['summary']+2 and calls['check']==before['check']
  assert page.locator('[data-action=version-select]').count()==2
  assert revisions[-1]['userInstruction']=='' and revisions[-1]['reviewNotes']==revisions[-2]['reviewNotes']
  behavior['fail']=False
  before=calls.copy()
  page.locator('[data-action=regenerate]').click();page.locator('[data-choice=own]').click()
  page.locator('dialog').get_by_role('button',name='开始生成',exact=True).click()
  assert calls==before
  page.locator('[data-action=regenerate]').click();page.locator('[data-choice=own]').click()
  page.locator('dialog textarea').fill('保留约定，简洁表达')
  page.locator('dialog').get_by_role('button',name='开始生成',exact=True).click()
  page.wait_for_function('document.querySelectorAll("[data-action=version-select]").length===3')
  assert revisions[-1]=={'userInstruction':'保留约定，简洁表达','reviewNotes':[]}
  page.locator('[data-action=regenerate]').click();page.locator('[data-choice=fresh]').click()
  page.wait_for_function('document.querySelectorAll("[data-action=version-select]").length===4')
  assert revisions[-1]=={'userInstruction':'','reviewNotes':[]}
  assert calls['summary']==before['summary']+2 and calls['check']==before['check']

  # Early preview also queues batch drafts exactly once and never stalls for save.
  page.locator('[data-action=discard]').click()
  page.locator('[data-tab=summary]').click();drawers();page.locator('#smm-batch-start').fill('0');page.locator('#smm-batch-end').fill('9');page.locator('[data-setting=batchSize]').fill('5');page.locator('[data-setting=batchClassification]').select_option('manual');page.locator('#smm-batch-hide').uncheck()
  hold['value']=True;page.locator('[data-action=batch-start]').click()
  for i in range(4):
   for _ in range(100):
    if held:break
    page.wait_for_timeout(30)
   assert len(held)==1,(i,len(held))
   if i==1:assert page.locator('.smm-save [data-action=approve]').is_disabled()
   route,response=held.pop();route.fulfill(json=response)
  hold['value']=False
  page.wait_for_function('document.querySelector("#smm-floating-progress")?.hidden===true')
  assert page.locator('[data-action=pending-select]').count()==1
  assert page.locator('.smm-save [data-action=approve]').is_enabled()
  page.locator('[data-tab=memories]').click();assert page.locator('[data-source-sort]').input_value()=='desc'
  # Clean pending drafts, then exercise deletion through actual checkbox/action/save path.
  page.evaluate("""()=>{const c=window.SillyTavern.getContext(),s=c.chatMetadata.st_memory_manager;localStorage.removeItem('st_memory_manager:session:character:mock.png::flow-test');const opts={...s.options,autoSummary:false,autoSecondary:false,autoTertiary:false,check:false,earlyDraft:false,autoHide:false,startFloor:26,autoStartFloor:26};s.options=opts;s.memories=[{id:'first',title:'前段',summary:'先前事实',details:{},keywords:[],sources:Array.from({length:20},(_,i)=>i),kind:'short',status:'active',level:1},{id:'last',title:'删除测试20-25',summary:'末段事实',details:{},keywords:[],sources:[20,21,22,23,24,25],kind:'short',status:'active',level:1}];s.batches=[{level:1,approved:true,floors:s.memories[0].sources,ids:['first']},{level:1,approved:true,floors:s.memories[1].sources,ids:['last']}];c.extensionSettings.st_memory_manager.autoSecondary=false;c.extensionSettings.st_memory_manager.autoTertiary=false;window.handlers.CHAT_CHANGED();}""")
  page.locator('[data-tab=memories]').click();drawers();page.locator('[data-pick=last]').check();page.locator('[data-action=memory-delete]').click()
  page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===1')
  page.locator('[data-tab=summary]').click();drawers()
  assert page.locator('#smm-start').input_value()=='20'
  assert page.locator('#smm-batch-start').input_value()=='20'
  assert '第20-' in page.locator('#smm-auto-status').text_content()
  page.evaluate('window.handlers.CHAT_CHANGED()');page.locator('[data-tab=summary]').click();drawers()
  assert page.locator('#smm-start').input_value()=='20'
  # Inactive count never blocks generation; switching back restores the explicit field.
  page.locator('[data-count-mode]').select_option('events')
  assert page.locator('[data-count-value]').is_hidden() and page.locator('[data-count-value]').is_disabled()
  page.locator('[data-count-mode]').select_option('count');assert page.locator('[data-count-value]').is_visible()
  page.locator('[data-count-value]').fill('5');page.locator('[data-count-mode]').select_option('events')
  # One batch creates five entries; saving it triggers consolidation despite another pending batch.
  page.evaluate("""()=>{const s=window.SillyTavern.getContext().chatMetadata.st_memory_manager;localStorage.removeItem('st_memory_manager:session:character:mock.png::flow-test');s.memories=[];s.batches=[];Object.assign(s.options,{startFloor:0,autoStartFloor:0,autoSecondary:true,secondaryCount:5,autoTertiary:false,autoSummary:false,check:false});window.handlers.CHAT_CHANGED();}""")
  page.locator('[data-tab=summary]').click();drawers();page.locator('#smm-batch-start').fill('0');page.locator('#smm-batch-end').fill('9');page.locator('[data-setting=batchSize]').fill('5');page.locator('[data-setting=batchClassification]').select_option('manual');page.locator('#smm-batch-hide').uncheck()
  behavior['multi']=True;before_summary=calls['summary'];before_check=calls['check']
  page.locator('[data-action=batch-start]').click();page.locator('[data-action=approve-all]').wait_for();page.wait_for_function('document.querySelector("#smm-floating-progress")?.hidden===true')
  assert calls['summary']==before_summary+2
  page.locator('.smm-save [data-action=approve]').click()
  page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===5')
  page.wait_for_function('document.querySelector("#smm-panel .smm-body")?.textContent.includes("二次总结") && !!document.querySelector("[data-action=pending-select]")')
  for _ in range(100):
   if calls['summary']>=before_summary+3:break
   page.wait_for_timeout(20)
  page.wait_for_function('document.querySelector("#smm-floating-progress")?.hidden===true')
  page.wait_for_timeout(200)
  assert calls['summary']==before_summary+3,(calls,before_summary)
  assert calls['check']==before_check
  assert page.locator('[data-action=pending-select]').count()==1
  behavior['multi']=False
  # Local keywords produce visible candidates without calling any API.
  page.locator('[data-tab=memories]').click();drawers();before_api=calls.copy()
  page.evaluate('(()=>{const ms=window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories;if(!ms.some(m=>m.kind==="long")&&ms.length)ms[0].kind="long"})()');page.locator('[data-action=keyword-health]').click();page.locator('.smm-keywords [data-generate]').click()
  page.wait_for_function('document.querySelector(".smm-keywords [role=alert]")?.textContent.includes("已补候选")')
  assert page.locator('.smm-keywords textarea').first.input_value()
  assert calls==before_api
  # Hold the keyword response to verify top-layer visibility and interactive cancel control.
  page.locator('.smm-keywords [data-method]').select_option('api');hold['value']=True
  page.locator('.smm-keywords [data-generate]').click()
  for _ in range(100):
   if held:break
   page.wait_for_timeout(20)
  assert len(held)==1
  assert page.locator('#smm-floating-progress').evaluate('(e)=>e.matches(":popover-open") && e.parentElement.matches(".smm-keywords")')
  assert page.locator('#smm-floating-progress [data-cancel]').evaluate('(e)=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e}')
  route,response=held.pop();route.fulfill(json=response);hold['value']=False
  page.locator('.smm-keywords > footer [data-cancel]').click()
  page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.forEach(m=>m.kind="short")')
  page.locator('[data-action=rehearsal]').click();page.locator('.smm-rehearsal [data-run]').click()
  assert page.locator('.smm-rehearsal [data-order]').count()==0
  text=page.locator('.smm-rehearsal [data-results]').inner_text()
  assert all(k in text for k in ['短期记忆','长期记忆','固定记忆','首次总结'])
  page.locator('.smm-rehearsal-body').evaluate('(e)=>e.scrollTop=e.scrollHeight')
  assert page.locator('.smm-rehearsal [data-close]').is_visible()
  page.locator('.smm-rehearsal [data-close]').click()
  # Verify actual toast timer selection through UI actions.
  page.evaluate("""()=>{const original=window.setTimeout;window.toastTimers=new Map();window.setTimeout=(f,ms,...args)=>{const id=original(f,ms,...args);window.toastTimers.set(id,ms);return id;}}""")
  page.locator('[data-tab=summary]').click();drawers();page.locator('[data-action=summary-refresh]').click()
  assert page.evaluate('window.toastTimers.get(document.getElementById("st_memory_manager-toast").timer)')==3500
  page.locator('#smm-start').fill('-1');page.locator('[data-action=usage-preview]').click()
  assert page.evaluate('window.toastTimers.get(document.getElementById("st_memory_manager-toast").timer)')==5000
  # Closed task log entries contain no eager serialized source; opening reads only that entry.
  page.locator('[data-tab=logs]').click();page.locator('[data-log-body]').first.wait_for(state='attached')
  assert page.locator('[data-log-body]').first.text_content()=='展开后读取完整内容…'
  first=page.locator('[data-log-body]').first
  first.evaluate('(e)=>{for(let p=e.parentElement;p;p=p.parentElement)if(p.tagName==="DETAILS")p.open=true}')
  page.wait_for_function('document.querySelector("[data-log-body]")?.dataset.loaded==="true"')
  page.screenshot(path=str(root/'output'/f'v072-regression-{width}.png'))
  # v0.7.2: legacy deletion paths preserve physical hidden state and rewind all three inputs.
  for variant in ['missing','stale','none']:
   page.evaluate("""(variant)=>{const c=window.SillyTavern.getContext(),s=c.chatMetadata.st_memory_manager;localStorage.removeItem('st_memory_manager:session:character:mock.png::flow-test');s.reopenedFloors=[];s.memories=[{id:'first',title:'前段',summary:'先前事实',details:{},keywords:[],sources:Array.from({length:20},(_,i)=>i),kind:'short',status:'active',level:1},{id:'last',title:'旧数据20-25',summary:'末段事实',details:{},keywords:[],sources:[20,21,22,23,24,25],kind:'short',status:'active',level:1}];s.batches=variant==='none'?[]:[{level:1,approved:true,floors:s.memories[0].sources,ids:['first']},{level:1,approved:true,floors:s.memories[1].sources,...(variant==='stale'?{ids:['obsolete']}: {})}];s.hidden=[20,21,22,23,24,25];c.chat.forEach((m,i)=>m.is_system=i>=20&&i<=25);Object.assign(s.options,{startFloor:26,autoStartFloor:26,autoSummary:false,autoSecondary:false,autoTertiary:false,check:false,earlyDraft:false,autoHide:false});window.handlers.CHAT_CHANGED();}""",variant)
   page.locator('[data-tab=memories]').click();drawers();page.locator('[data-pick=last]').check();page.locator('[data-action=memory-delete]').click()
   page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===1')
   page.locator('[data-tab=summary]').click();drawers()
   assert page.locator('#smm-start').input_value()=='20',variant
   assert page.locator('#smm-batch-start').input_value()=='20',variant
   assert '第20-' in page.locator('#smm-auto-status').text_content(),variant
   assert '尚未总结：第20-29楼' in page.locator('.smm-progress-board').first.inner_text(),variant
   assert page.evaluate('window.SillyTavern.getContext().chat.filter(m=>m.is_system).length')==6
   assert page.evaluate('JSON.stringify(window.SillyTavern.getContext().chatMetadata.st_memory_manager.hidden)')=='[20,21,22,23,24,25]'
   page.evaluate('window.handlers.CHAT_CHANGED()');page.locator('[data-tab=summary]').click()
   assert page.locator('#smm-start').input_value()=='20'
  # Explicit completion proposal; failed save must revert both appended marker and new summary.
  page.evaluate("""()=>{const c=window.SillyTavern.getContext(),s=c.chatMetadata.st_memory_manager;localStorage.removeItem('st_memory_manager:session:character:mock.png::flow-test');s.memories=[{id:'old',title:'铜印约定',summary:'旧摘要原样保留',details:{promises:'阿宁归还铜印\\n明日赴约',time:'昨日',place:'青石桥'},keywords:['铜印','阿宁'],sources:[1],kind:'short',status:'active',level:1}];s.batches=[];s.reopenedFloors=[];s.hidden=[];c.chat.forEach(m=>m.is_system=false);c.chat[21].mes='<CONTENT>阿宁已经归还铜印，约定已完成。</CONTENT>';Object.assign(s.options,{startFloor:20,autoStartFloor:20,includeMemories:true,autoSummary:false,autoSecondary:false,autoTertiary:false,check:false,earlyDraft:false,autoHide:false});window.failMetadata=false;c.saveMetadata=async()=>{if(window.failMetadata)throw Error('模拟保存失败');window.savedStore=structuredClone(c.chatMetadata)};window.handlers.CHAT_CHANGED();}""")
  behavior['status']=True;page.locator('[data-tab=summary]').click();drawers();page.locator('#smm-start').fill('20');page.locator('#smm-end').fill('21');page.locator('[data-action=summarize]').click()
  page.locator('[data-status-update]').wait_for();assert not page.locator('[data-status-update]').is_checked()
  assert '第21楼证据' in page.locator('.smm-status-updates').inner_text()
  # All draft footer actions stay visible without scrolling the memory list to the end.
  for edge in [0,100000]:
   page.evaluate('(n)=>document.querySelector("#smm-panel .smm-body").scrollTop=n',edge)
   for act in ['approve','regenerate','discard']:
    b=page.locator('.smm-save [data-action='+act+']').bounding_box()
    assert b and b['y']>=0 and b['y']+b['height']<=900,(width,act,b)
  page.evaluate('document.querySelector("#smm-panel .smm-body").scrollTop=0')
  page.screenshot(path=str(root/'output'/f'v072-status-update-{width}.png'))
  page.locator('[data-status-update]').check();page.evaluate('window.failMetadata=true');page.locator('.smm-save [data-action=approve]').click()
  page.wait_for_function('document.getElementById("st_memory_manager-toast")?.textContent.includes("模拟保存失败")')
  assert page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length')==1
  assert page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories[0].details.promises')=='阿宁归还铜印\n明日赴约'
  page.evaluate('window.failMetadata=false');page.locator('.smm-save [data-action=approve]').click()
  page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===2')
  value=page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories[0]')
  assert value['details']['promises']=='阿宁归还铜印（已完成）\n明日赴约'
  assert value['summary']=='旧摘要原样保留' and value['details']['time']=='昨日' and value['details']['place']=='青石桥'
  assert value['statusHistory'][0]['evidence'][0]['sourceFloor']==21
  # A title-specific update notice is delivered even if followed by the normal save notice.
  assert page.evaluate("document.getElementById('st_memory_manager-toast')?.textContent.includes('铜印约定') && document.getElementById('st_memory_manager-toast')?.textContent.includes('已更新')")
  behavior['status']=False
  # Move selected short records; they must not remain checked in long or after changing pages.
  page.locator('[data-tab=memories]').click();drawers();page.locator('[data-pick=old]').check();page.locator('[data-action=memory-add]').click();page.locator('.smm-destination [value=long]').check();page.locator('.smm-destination').get_by_role('button',name='确定添加').click();page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.find(m=>m.id==="old").kind==="long"');page.wait_for_function('!document.querySelector("[data-pick]:checked")');drawers()
  assert page.locator('[data-pick]:checked').count()==0
  assert page.locator('.smm-group > summary [data-action=keywords]').count()==1
  page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.find(m=>m.id==="old").keywords=[]')
  drawer=page.locator('.smm-group').filter(has=page.locator('summary [data-action=keywords]')).first
  was=drawer.evaluate('e=>e.open');page.locator('.smm-group > summary [data-action=keywords]').click();page.locator('.smm-keywords').wait_for()
  assert drawer.evaluate('e=>e.open')==was
  # Empty alert no longer creates an opaque bar; footer never follows the scroll position.
  assert page.locator('.smm-keywords [role=alert]').evaluate('e=>getComputedStyle(e).display')=='none'
  for pos in [0,99999]:
   page.locator('.smm-keywords .smm-dialog-body').evaluate('(e,n)=>e.scrollTop=n',pos)
   r=page.locator('.smm-keywords').bounding_box();b=page.locator('.smm-keywords .smm-dialog-footer [data-save]').bounding_box();assert r['y']<=b['y'] and b['y']+b['height']<=r['y']+r['height']+1
  page.screenshot(path=str(root/'output'/f'v072-keyword-footer-{width}.png'))
  page.locator('.smm-keywords [data-cancel]').click()
  # AI classification preserves long suggestions even after check failure; manual keeps user choice.
  page.evaluate("""()=>{const c=window.SillyTavern.getContext(),s=c.chatMetadata.st_memory_manager;localStorage.removeItem('st_memory_manager:session:character:mock.png::flow-test');s.memories=[];s.batches=[];s.reopenedFloors=[];Object.assign(s.options,{startFloor:0,autoStartFloor:0,autoSummary:false,autoSecondary:false,autoTertiary:false,check:false,earlyDraft:false,autoHide:false});window.handlers.CHAT_CHANGED();}""")
  page.locator('[data-tab=summary]').click();drawers();page.locator('#smm-batch-start').fill('0');page.locator('#smm-batch-end').fill('9');page.locator('[data-setting=batchSize]').fill('5');page.locator('[data-setting=batchClassification]').select_option('ai');page.locator('#smm-batch-hide').uncheck();page.locator('[data-action=batch-start]').click()
  page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===2')
  assert page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.every(m=>m.kind==="long"&&m.keywords.length===2)')
  # Check failure must not discard the AI-selected category when queued for review.
  behavior['checkFail']=True
  page.evaluate("""()=>{const s=window.SillyTavern.getContext().chatMetadata.st_memory_manager;localStorage.removeItem('st_memory_manager:session:character:mock.png::flow-test');s.memories=[];s.batches=[];s.reopenedFloors=[];Object.assign(s.options,{startFloor:0,autoStartFloor:0,check:true,earlyDraft:false});window.handlers.CHAT_CHANGED();}""")
  page.locator('[data-tab=summary]').click();drawers();page.locator('#smm-batch-start').fill('0');page.locator('#smm-batch-end').fill('9');page.locator('[data-setting=batchSize]').fill('5');page.locator('[data-setting=batchClassification]').select_option('ai');page.locator('#smm-batch-hide').uncheck();page.locator('[data-action=batch-start]').click()
  page.locator('[data-action=approve-all]').wait_for();page.wait_for_function('document.querySelector("#smm-floating-progress")?.hidden===true')
  assert page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length')==0
  assert '长期记忆' in page.locator('.smm-card summary small').first.inner_text()
  behavior['checkFail']=False
  # Mixed category confirmation queues matching kinds and still completes both batches.
  page.evaluate("""()=>{const s=window.SillyTavern.getContext().chatMetadata.st_memory_manager;localStorage.removeItem('st_memory_manager:session:character:mock.png::flow-test');s.memories=[];s.batches=[];s.reopenedFloors=[];Object.assign(s.options,{startFloor:0,autoStartFloor:0,check:false,earlyDraft:false});window.handlers.CHAT_CHANGED();}""")
  page.locator('[data-tab=summary]').click();drawers();page.locator('#smm-batch-start').fill('0');page.locator('#smm-batch-end').fill('9');page.locator('[data-setting=batchSize]').fill('5');page.locator('[data-setting=batchClassification]').select_option('mixed');page.locator('[data-batch-manual=long]').check();page.locator('#smm-batch-hide').uncheck();before=calls['summary'];page.locator('[data-action=batch-start]').click()
  page.locator('[data-action=approve-all]').wait_for();page.wait_for_function('document.querySelector("#smm-floating-progress")?.hidden===true')
  assert calls['summary']==before+2
  assert page.evaluate('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length')==0
  assert '长期记忆' in page.locator('.smm-card summary small').first.inner_text()
  # Clear reviewed queue before checking cancellation of another two-batch task.
  page.evaluate("""()=>{const s=window.SillyTavern.getContext().chatMetadata.st_memory_manager;localStorage.removeItem('st_memory_manager:session:character:mock.png::flow-test');Object.assign(s.options,{check:false});window.handlers.CHAT_CHANGED();}""")
  # Stage counters are computed from the current active and eligible records.
  page.evaluate("""()=>{const s=window.SillyTavern.getContext().chatMetadata.st_memory_manager;s.memories=Array.from({length:10},(_,i)=>({id:'org'+i,title:'整理测试'+i,summary:'阿宁赴约',details:{},keywords:[],sources:[i],kind:'short',status:'active',level:1}));s.batches=[];Object.assign(s.options,{autoSecondary:false,autoTertiary:false,oldPolicy2:'archive',oldPolicy3:'archive'});window.handlers.CHAT_CHANGED();}""")
  page.locator('[data-tab=organize]').click();drawers()
  stage1=page.locator('[data-entry=organization-1] > summary');stage2=page.locator('[data-entry=organization-2] > summary')
  assert '有效 10 条 · 可整理 10 条' in stage1.inner_text()
  for i in range(5):page.locator('[data-org-pick="1"]').nth(i).check()
  page.locator('[data-action=org-merge2]').click();page.locator('[data-choice=later]').click()
  page.locator('.smm-save [data-action=approve]').click();page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===11')
  page.locator('[data-tab=organize]').click()
  assert '有效 5 条 · 可整理 5 条' in stage1.inner_text()
  assert '有效 1 条 · 可整理 1 条' in stage2.inner_text()
  page.evaluate('window.handlers.CHAT_CHANGED()')
  assert '有效 5 条 · 可整理 5 条' in stage1.inner_text()
  page.locator('[data-tab=memories]').click()
  assert page.locator('#smm-panel > nav button').count()==5
  assert page.locator('[data-action=minimize]').count()==0
  assert page.locator('[data-action=search-prev]').evaluate('e=>getComputedStyle(e).borderTopWidth')=='0px'
  assert page.locator('#smm-search').evaluate('e=>getComputedStyle(e).borderTopWidth')=='1px'
  page.evaluate('document.getElementById("st_memory_manager-toast")?.remove()')
  assert page.locator('[data-action=check-short-all]').count()==0
  assert page.locator('[data-action=export],[data-action=memory-import]').count()==0
  assert page.locator('.smm-memory-operations button').all_text_contents()==['新增','添加到','归档／恢复','删除','清空']
  assert page.locator('.smm-memory-tools button').all_text_contents()==['有效记忆','归档','记忆发送预演']
  assert page.locator('.smm-keyword-tools button').all_text_contents()==['补充关键词','关键词检测']
  left=page.locator('.smm-memory-topline [data-source-sort]').bounding_box()
  right=page.locator('.smm-memory-topline [data-memory-scope]').bounding_box()
  assert abs(left['y']-right['y'])<1 and left['x']<right['x']
  assert abs(left['width']-right['width'])<1
  search=page.locator('.smm-searchbar').bounding_box()
  assert search['y']+search['height']<=left['y']
  tools=page.locator('.smm-memory-tools button').all()
  widths=[b.bounding_box()['width'] for b in tools]
  assert max(widths)-min(widths)<1
  assert page.locator('.smm-memory-workspace .smm-memory-operations button').count()==5
  assert page.locator('.smm-memory-workspace > .smm-group').count()==3
  assert page.locator('.smm-memory-workspace').evaluate('e=>getComputedStyle(e).backgroundColor')!=page.locator('#smm-panel').evaluate('e=>getComputedStyle(e).backgroundColor')

  before_api=calls.copy()
  page.locator('[data-action=memory-add]').click()
  page.wait_for_function('document.getElementById("st_memory_manager-toast")?.textContent.includes("请先勾选")')
  assert page.locator('.smm-destination').count()==0 and calls==before_api
  drawers();page.locator('[data-pick]').first.check()
  page.locator('[data-action=memory-add]').click()
  assert page.locator('.smm-destination [name=destination]').count()==4
  page.locator('.smm-destination [data-cancel]').click()
  assert page.locator('[data-pick]:checked').count()==1
  page.locator('[data-action=memory-add]').click();page.locator('.smm-destination [value=attic]').check()
  page.locator('.smm-destination').get_by_role('button',name='确定添加').click()
  page.wait_for_function('window.SillyTavern.getContext().extensionSettings.st_memory_manager.attics["mock.png"].memories.length===1')
  page.wait_for_function('!document.querySelector("[data-pick]:checked")')
  before_api=calls.copy()
  page.locator('[data-memory-scope]').select_option('attic')
  assert page.locator('[data-memory-scope]').input_value()=='attic'
  assert page.locator('.smm-card').count()==1
  page.locator('[data-memory-scope]').select_option('chat')
  assert page.locator('.smm-card').count()==6
  assert calls==before_api
  page.evaluate('document.getElementById("st_memory_manager-toast")?.remove()')
  page.screenshot(path=str(root/'output'/f'memory-layout-v2-dark-{width}.png'))
  page.locator('[data-action=settings-open]').click();drawers()
  assert page.locator('[data-action=export]').count()==1 and page.locator('[data-action=memory-import]').count()==1
  assert page.locator('[data-action=check-short-all]').count()==0
  page.locator('[data-tab=memories]').click()

  page.locator('[data-tab=organize]').click();drawers()
  page.locator('[data-org-pick="2"]').check();page.locator('[data-action=org-merge3]').click();page.locator('[data-choice=later]').click()
  page.locator('.smm-save [data-action=approve]').click();page.wait_for_function('window.SillyTavern.getContext().chatMetadata.st_memory_manager.memories.length===12')
  page.locator('[data-tab=organize]').click()
  assert '有效 0 条 · 可整理 0 条' in stage2.inner_text()
  assert '有效 1 条' in page.locator('[data-entry=organization-3] > summary').inner_text()
  page.locator('[data-action=settings-open]').click();drawers()
  page.evaluate("""()=>{const style=document.createElement('style');style.id='mock-host-input';style.textContent='input,textarea,select{background:black!important;color:white!important}';document.head.append(style);document.body.style.setProperty('--SmartThemeChatTintColor','#badcfe');document.body.style.setProperty('--SmartThemeBodyColor','#123456');}""")
  page.locator('[data-setting=themePreset]').select_option('paper')
  assert page.locator('[data-setting=model]').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(255, 250, 241)'
  assert page.locator('[data-setting=model]').evaluate('e=>getComputedStyle(e).color')=='rgb(51, 47, 43)'
  page.locator('[data-setting=themePreset]').select_option('tavern')
  assert '#badcfe' in page.locator('[data-setting=model]').evaluate('e=>getComputedStyle(e).getPropertyValue("--smm-field-bg")')
  assert page.locator('[data-setting=model]').evaluate('e=>getComputedStyle(e).color')=='rgb(18, 52, 86)'
  page.locator('[data-setting=themePreset]').select_option('paper')
  page.locator('[data-action=settings-save]').click()
  page.locator('[data-tab=memories]').click();page.locator('[data-action=manual]').click()
  assert page.locator('.smm-editor input[name=title]').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(255, 250, 241)'
  page.locator('.smm-editor [data-dismiss]').click()
  page.evaluate('document.getElementById("st_memory_manager-toast")?.remove()')
  page.screenshot(path=str(root/'output'/f'memory-layout-v2-paper-{width}.png'))
  page.evaluate("document.body.style.setProperty('--SmartThemeBlurTintColor','#eaf0f7')")
  for theme in ['soft','paper','contrast','tavern']:
   page.locator('[data-action=settings-open]').click();drawers()
   page.locator('[data-setting=themePreset]').select_option(theme)
   page.locator('[data-tab=memories]').click()
   page.evaluate("document.querySelectorAll('#smm-panel details.smm-group').forEach(d=>d.open=false);document.getElementById('st_memory_manager-toast')?.remove()")
   style=page.locator('#smm-panel').evaluate("""e=>{const search=e.querySelector('#smm-search'),workspace=e.querySelector('.smm-memory-workspace'),range=e.querySelector('[data-memory-scope]');return {theme:e.dataset.theme,searchWidth:search.getBoundingClientRect().width,searchHeight:search.getBoundingClientRect().height,rangeBg:getComputedStyle(range).backgroundColor,rangeInk:getComputedStyle(range).color,searchBg:getComputedStyle(search).backgroundColor,workspaceBg:getComputedStyle(workspace).backgroundColor,panelBg:getComputedStyle(e).getPropertyValue('--smm-bg'),horizontalOverflow:e.scrollWidth>e.clientWidth}}""")
   assert style['theme']==theme and style['searchWidth']<=220.1 and style['searchHeight']<=32.1 and not style['horizontalOverflow'],style
   expected={'soft':'rgb(241, 244, 248)','paper':'rgb(51, 47, 43)','contrast':'rgb(255, 255, 255)','tavern':'rgb(18, 52, 86)'}
   assert style['rangeInk']==expected[theme],style
   assert style['workspaceBg']!='rgba(0, 0, 0, 0)',style
   theme_checks.append(style)
   page.screenshot(path=str(root/'output'/f'memory-v073-theme-{theme}-{width}.png'))
  page.locator('[data-action=settings-open]').click();drawers();page.locator('[data-setting=themePreset]').select_option('paper')
  page.locator('[data-tab=memories]').click()
  drawers();page.locator('[data-pick]').first.check();page.locator('[data-action=memory-add]').click()
  page.screenshot(path=str(root/'output'/f'memory-layout-v2-add-{width}.png'))
  page.locator('.smm-destination [data-cancel]').click()
  page.locator('[data-pick]:checked').uncheck()

  page.evaluate("document.getElementById('mock-host-input').remove()")
  # Hold a request to resize, drag, cancel, and verify persisted dimensions and stopped batch queue.
  page.locator('[data-tab=summary]').click();drawers();page.locator('#smm-batch-start').fill('10');page.locator('#smm-batch-end').fill('19');page.locator('[data-setting=batchSize]').fill('5');hold['value']=True;before=calls['summary'];page.locator('[data-action=batch-start]').click()
  for _ in range(100):
   if held:break
   page.wait_for_timeout(20)
  page.locator('#smm-floating-progress [data-larger]').click();page.wait_for_timeout(200)
  size=page.locator('#smm-floating-progress').bounding_box();assert size['width']>=300
  box=page.locator('#smm-floating-progress header strong').bounding_box();page.mouse.move(box['x']+20,box['y']+5);page.mouse.down();page.mouse.move(box['x']+25,box['y']+45);page.mouse.up();page.wait_for_timeout(200)
  persisted=page.evaluate('JSON.parse(localStorage.getItem("st_memory_manager:window-size-v1:progress"))');assert persisted['width']==size['width'] and persisted['position']['top']>0
  page.screenshot(path=str(root/'output'/f'v072-progress-{width}.png'))
  page.locator('#smm-floating-progress [data-cancel]').click();page.get_by_role('button',name='继续下一批',exact=True).wait_for();page.wait_for_timeout(200);assert calls['summary']==before+1
  hold['value']=False
  for route,response in held:
   try:route.fulfill(json=response)
   except Exception:pass
  held.clear()
  assert page.locator('#smm-floating-progress').is_hidden()
  # Clear the previous paused batch and confirm two manual HTTP requests can be active together.
  page.locator('[data-action=batch-cancel]').click()
  page.locator('[data-tab=summary]').click();drawers();hold['value']=True
  def submit_summary(start,end):
   page.locator('#smm-start').fill(str(start));page.locator('#smm-end').fill(str(end))
   page.locator('#smm-hide1').uncheck()
   page.locator('[data-action=summarize]').click()
  def wait_held(n):
   for _ in range(140):
    if len(held)>=n:break
    page.wait_for_timeout(25)
   assert len(held)==n,len(held)
  # Any previously retained draft can remain in pending while new work runs.
  submit_summary(10,11)
  new=page.locator('dialog[open] [data-choice=new]')
  if new.count():new.click()
  wait_held(1)
  submit_summary(12,13);wait_held(2)
  statuses=page.locator('.smm-progress-board [data-smm-task-status]').first
  assert statuses.get_by_role('button',name='取消',exact=True).count()==2
  assert '第10-11楼' in statuses.inner_text() and '第12-13楼' in statuses.inner_text()
  page.locator('#smm-floating-progress [data-close]').click()
  failed,_=held.pop(0);failed.fulfill(json={'error':{'message':'模拟并发失败','code':'test_failure'}})
  page.wait_for_function("document.querySelectorAll('.smm-progress-board [data-task]').length===1")
  assert '第12-13楼' in statuses.inner_text()
  # A third request can start as soon as the failure releases one slot.
  submit_summary(14,15);wait_held(2)
  if page.locator('#smm-floating-progress [data-close]').is_visible():page.locator('#smm-floating-progress [data-close]').click()
  statuses.scroll_into_view_if_needed()
  page.screenshot(path=str(root/'output'/f'v075-concurrent-{width}.png'))
  statuses.get_by_text('第14-15楼',exact=False).get_by_role('button',name='取消',exact=True).click()
  page.wait_for_function("document.querySelectorAll('.smm-progress-board [data-task]').length===1")
  survivor,response=held.pop(0);survivor.fulfill(json=response)
  cancelled,response=held.pop(0)
  try:cancelled.fulfill(json=response)
  except Exception:pass
  page.wait_for_function("document.querySelector('[data-tab=draft]').classList.contains('active') && document.querySelector('header .smm-actions')")
  page.locator('[data-tab=summary]').click()
  page.wait_for_function("document.querySelector('[data-smm-task-status]')?.textContent==='空闲'")
  assert page.locator('#smm-floating-progress').is_hidden()
  # Two successful jobs retain two independent drafts.
  submit_summary(16,17)
  if new.count():new.click()
  wait_held(1)
  submit_summary(18,19);wait_held(2)
  for route,response in held:route.fulfill(json=response)
  held.clear()
  page.locator('[data-tab=draft]').click()
  page.wait_for_function("""()=>{const raw=localStorage.getItem('st_memory_manager:session:character:mock.png::flow-test');const v=JSON.parse(raw||'null');const ranges=[v?.draft,...(v?.pendingDrafts||[]).map(e=>e.draft),...(v?.draftVersions||[])].map(x=>x?.rangeLabel);return ranges.includes('第16-17楼')&&ranges.includes('第18-19楼');}""")
  # A live request must not restore any draft after a clear.
  page.locator('[data-tab=summary]').click()
  submit_summary(20,21)
  if new.count():new.click()
  wait_held(1)
  # Drop all chat-owned data, including archived memories, logs and snapshots. Keep other chats and the attic.
  page.evaluate("""async()=>{const c=window.SillyTavern.getContext(),ns='st_memory_manager',st=c.chatMetadata[ns];st.ignoredFloors=[16];st.recall={old:{until:91}};st.memories.push({id:'clear-archive',title:'本聊归档',summary:'本聊归档',status:'archived',kind:'short',sources:[16],details:{},keywords:[]});c.chat[0].is_system=true;const shared=c.extensionSettings[ns].attics??={};shared['mock.png']={memories:[{id:'surviving-attic',title:'保留阁楼',summary:'保留阁楼',status:'active',kind:'fixed',sources:[],details:{},keywords:[]}]};localStorage.setItem(ns+':session:other-chat','other session');const DB=await import('/runtime.js');await DB.record('logs',{id:'other-log',chat:'other-chat'});await DB.record('snapshots',{id:'other-snapshot',chat:'other-chat'});}""")
  page.locator('[data-tab=memories]').click()
  page.locator('[data-memory-scope]').select_option('attic')
  page.locator('[data-action=memory-clear]').click()
  page.wait_for_function("""()=>{const c=window.SillyTavern.getContext(),s=c.chatMetadata.st_memory_manager;return !s.memories.length&&!s.batches.length&&!s.ignoredFloors&&Object.keys(s.recall).length===0&&s.options.startFloor===0&&s.options.autoStartFloor===0&&document.querySelector('[data-memory-scope]')?.value==='chat'}""")
  route,response=held.pop(0)
  try:route.fulfill(json=response)
  except Exception:pass
  hold['value']=False
  assert page.evaluate("""async()=>{const c=window.SillyTavern.getContext(),db=await import('/runtime.js');return c.chat[0].is_system&&c.extensionSettings.st_memory_manager.attics['mock.png'].memories[0].id==='surviving-attic'&&localStorage.getItem('st_memory_manager:session:other-chat')==='other session'&&(await db.records('logs')).every(x=>x.chat==='other-chat')&&(await db.records('snapshots')).every(x=>x.chat==='other-chat')&&(await db.records('logs')).some(x=>x.id==='other-log')&&(await db.records('snapshots')).some(x=>x.id==='other-snapshot');}""")
  page.locator('[data-tab=draft]').click()
  assert '没有待确认草稿' in page.locator('.smm-body').inner_text()
  page.locator('[data-tab=summary]').click()
  assert page.locator('#smm-start').input_value()=='0'
  assert '开始自动总结' in page.locator('#smm-auto-status').text_content()
  assert errors==[],errors
  results.append({'width':width,'calls':calls,'defaults':True,'continuousBatches':True,'saveAll':True,'ignoreGaps':True,'autoCursor':True,'tourCenteredSettingsFirst':True,'fixedFooter':True,'legacyDeleteHiddenUntouched':True,'statusUpdateRollbackAndNotice':True,'clearSelection':True,'aiAndMixedClassification':True,'resizableCancellableProgress':True,'themeChecks':theme_checks})
  page.close()
 browser.close();(root/'output'/'v072-browser-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(results,ensure_ascii=False))
server.shutdown()
