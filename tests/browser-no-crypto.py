# Synthetic startup checks for legacy HTTP WebViews. No user data or external API is used.
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

def context_script(valid=True):
 return """()=>{
  document.body.innerHTML='<div id="extensionsMenu"></div>';
  const c=%s;
  window.SillyTavern={getContext:()=>c};
 }""" % ("{chat:[],chatId:'legacy-http',characterId:0,characters:[{avatar:'mock.png'}],chatMetadata:{},extensionSettings:{},eventTypes:{},eventSource:{on(){}},getRequestHeaders:()=>({}),saveMetadata:async()=>{},saveSettingsDebounced(){},setExtensionPrompt(){}}" if valid else "{extensionSettings:{}}")

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
 page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("Object.defineProperty(globalThis,'crypto',{configurable:true,value:undefined})")
 page.goto(url+'/package.json');page.evaluate(context_script())
 page.evaluate("import('/index.js?legacy-no-crypto')")
 page.locator('#smm-entry').wait_for();page.locator('.smm-launcher-ball').wait_for()
 assert page.evaluate('globalThis.crypto') is None
 assert page.locator('#smm-entry-error').count()==0 and errors==[],errors
 broken=browser.new_page();broken.goto(url+'/package.json');broken.evaluate(context_script(False))
 broken.evaluate("import('/index.js?visible-startup-error')")
 error_entry=broken.locator('#smm-entry-error');error_entry.wait_for()
 assert '当前页面未提供酒馆聊天接口' in error_entry.get_attribute('title')
 print('legacy HTTP startup and visible startup diagnostics passed')
 browser.close()
server.shutdown()
