import base64
import functools
import http.server
import json
import os
import threading
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

root = Path(__file__).resolve().parent.parent
version = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))['version']
key = 'st_memory_manager:launchers'

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

with http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root))) as server, sync_playwright() as p:
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    browser = p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
    for width, touch in [(1280, False), (390, True)]:
        page = browser.new_page(viewport={'width': width, 'height': 860}, has_touch=touch, is_mobile=touch)
        page.set_default_timeout(7000)
        touch_session = page.context.new_cdp_session(page) if touch else None
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('**/launcher-test', lambda route: route.fulfill(content_type='text/html', body='''<!doctype html>
          <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
          <link rel="stylesheet" href="/style.css"></head><body><div id="extensionsMenu"></div><script>
          const c={chat:[],chatId:'launcher-fixture',chatMetadata:{},extensionSettings:{},eventTypes:{},
          eventSource:{on(){}},getRequestHeaders(){return {}},saveMetadata(){},saveSettingsDebounced(){},setExtensionPrompt(){}};
          window.SillyTavern={getContext:()=>c};localStorage.setItem('st_memory_manager:tour-seen','1');
          </script><script type="module" src="/index.js"></script></body></html>'''))

        def saved():
            return page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))', key)

        ball = page.locator('.smm-launcher-ball')
        edge = page.locator('.smm-launcher-edge')
        panel = page.locator('#smm-panel')
        ball_open = ball.locator('.smm-launcher-open')
        edge_open = edge.locator('.smm-launcher-open')
        control = lambda name: page.locator(f'#smm-panel [data-launcher={name}]')
        def tap(locator):
            if not touch:
                locator.click()
                return
            locator.scroll_into_view_if_needed()
            box = locator.bounding_box()
            touch_session.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':box['x']+box['width']/2,'y':box['y']+box['height']/2}]})
            touch_session.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
        def drag(locator, dx, dy):
            box = locator.bounding_box()
            x, y = box['x'] + box['width']/2, box['y'] + box['height']/2
            if touch:
                touch_session.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
                for i in range(1, 6):
                    touch_session.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x+dx*i/5, 'y': y+dy*i/5}]})
                touch_session.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
            else:
                page.mouse.move(x,y); page.mouse.down(); page.mouse.move(x+dx,y+dy,steps=6); page.mouse.up()

        def settings():
            tap(page.get_by_role('button', name='设置', exact=True))
            return page.locator('#smm-panel details summary').filter(has_text='插件开关')

        def close_panel():
            tap(page.get_by_role('button', name='关闭面板', exact=True))
            panel.wait_for(state='hidden')

        page.goto(url+'/launcher-test')
        ball_open.wait_for(); assert not edge.is_visible() and ball.get_by_role('button').count()==1
        assert ball_open.evaluate("(e)=>[getComputedStyle(e).backgroundColor,getComputedStyle(e).color]")==['rgb(0, 0, 0)','rgb(255, 255, 255)']
        bounds = ball_open.bounding_box()
        assert abs(bounds['x']+26-width/2)<1 and abs(bounds['y']+26-430)<1, bounds
        drag(ball_open, -65, 65); assert not panel.is_visible() and saved()['x']<.5
        page.reload(); ball_open.wait_for(); assert saved()['x']<.5
        tap(page.locator('#smm-entry')); drawer = settings()
        assert not control('ballOn').is_visible(); tap(drawer)
        control('ballOn').uncheck(); close_panel(); page.reload(); page.locator('#smm-entry').wait_for(); assert not ball.is_visible()
        tap(page.locator('#smm-entry')); drawer = settings(); tap(drawer)
        assert control('ballOn').is_visible() and not control('ballOn').is_checked()
        assert page.locator('[data-setting=pluginEnabled]').is_visible() and control('edgeOn').is_visible()
        page.evaluate("import('/index.js?duplicate=1')")
        assert ball.count()==edge.count()==page.locator('#smm-entry').count()==1 and control('ballOn').is_visible()
        control('ballOn').check(); control('edgeOn').check()
        assert not control('ballReset').is_visible() and not control('edgeReset').is_visible()
        tap(drawer.locator('xpath=..').locator('.smm-launcher-controls summary').first)
        tap(control('ballReset'))
        assert saved()['x']==saved()['y']==.5 and edge.get_attribute('data-side')=='right'
        assert edge.get_by_role('button').count()==1 and saved()['edgeY']==.5
        assert edge_open.evaluate("(e)=>getComputedStyle(e).opacity")=='0.57'
        if os.getenv('SMM_UI_PREVIEW') and width==390:
            close_panel()
            page.add_style_tag(content='body{background:#252a32;color:#d7e0e9} .fa-layer-group::before{content:"";display:inline-block;width:1.05em;height:1.05em;background:currentColor;clip-path:polygon(50% 0,100% 26%,50% 52%,0 26%,50% 0,50% 59%,92% 38%,100% 44%,50% 71%,0 44%,8% 38%,50% 59%,50% 79%,92% 57%,100% 64%,50% 94%,0 64%,8% 57%,50% 79%)}')
            page.screenshot(path=str(root/'output'/'ui-01-launchers.png'))
            tap(page.locator('#smm-entry')); panel.wait_for()
        control('text').fill('记忆'); control('text').press('Tab'); assert ball_open.inner_text()=='记忆'
        control('color').fill('#e9d5a3'); assert ball_open.evaluate('(e)=>e.style.backgroundColor')=='rgb(233, 213, 163)'
        png = base64.b64decode(page.evaluate("document.createElement('canvas').toDataURL().split(',')[1]"))
        control('image').set_input_files({'name':'fixture.png','mimeType':'image/png','buffer':png})
        expect(page.locator('[data-launcher-status]')).to_have_text('图片已保存', timeout=5000)
        page.wait_for_function("document.querySelector('.smm-launcher-ball img')?.naturalWidth===128")
        tap(control('imageClear')); assert ball_open.inner_text()=='记忆'
        close_panel(); tap(ball_open); panel.wait_for()
        close_panel()
        drag(edge_open, -(width-40), -45); assert edge.get_attribute('data-side')=='left' and not panel.is_visible()
        drag(edge_open, 65, 0); panel.wait_for(); assert edge.get_attribute('data-side')=='left'
        close_panel(); tap(edge_open); panel.wait_for()
        drawer=settings()
        if not control('edgeOn').is_visible(): tap(drawer)
        if not control('edgeReset').is_visible(): tap(control('edgeOn').locator('xpath=..').locator('summary'))
        tap(control('edgeReset')); assert edge.get_attribute('data-side')=='right' and saved()['edgeY']==.5
        control('edgeOn').uncheck(); close_panel(); assert not edge.is_visible()
        page.evaluate('([key,old])=>localStorage.setItem(key,JSON.stringify({...JSON.parse(localStorage.getItem(key)),version:old,ballOn:false,x:.1,y:.8}))', [key,'0.7.5'])
        page.reload(); ball_open.wait_for()
        assert saved()['version']==version and saved()['x']==saved()['y']==.5 and not edge.is_visible()
        assert ball_open.inner_text()=='记忆' and ball.get_by_role('button').count()==1 and not errors, errors
        assert ball_open.evaluate('(e)=>e.style.backgroundColor')=='rgb(233, 213, 163)'
        page.evaluate('(key)=>localStorage.setItem(key,JSON.stringify({version:"0.7.6",color:"#365b7c",ballOn:true}))',key)
        page.reload();ball_open.wait_for()
        assert ball_open.evaluate('(e)=>e.style.backgroundColor')=='rgb(0, 0, 0)'
        print(f'{width}px: install, upgrade, persistence, close, reset, appearance, menu, drag, snap and open passed')
        page.close()
    server.shutdown()
