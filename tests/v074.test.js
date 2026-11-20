import test from 'node:test';
import assert from 'node:assert/strict';
import {DEFAULTS,FIELDS,validateDraft,summaryPrompt,buildInjection} from '../core.js';
import {formatExample} from '../formats.js';
import {summarySchema} from '../output-contract.js';
import {defaultProfileOptions} from '../default-settings.js';
import {settingsView} from '../settings-ui.js';

test('characters survive all three formats, serialization and injection, respecting each mode',()=>{
 assert.equal(FIELDS.characters,'人物');assert.equal(DEFAULTS.modes.characters,'separate');
 assert.equal(defaultProfileOptions().modes.characters,'separate');
 for(const outputMode of ['json','tags','plain']){
  const s={...structuredClone(DEFAULTS),outputMode,summaryLevel:1};
  const source=[{floor:0,text:'人物',role:'user'},{floor:1,text:'人物',role:'assistant'}];
  const item=validateDraft(formatExample(s),source,s)[0];
  assert.equal(item.details.characters,'人物',outputMode);
  assert.equal(JSON.parse(JSON.stringify(item)).details.characters,'人物');
  assert.ok(buildInjection([{...item,mode:'full'}],s).text.includes('人物：人物'));
  assert.ok(!buildInjection([{...item,mode:'full'}],{...s,sendFields:{...s.sendFields,characters:false}}).text.includes('人物：人物'));
  for(const mode of ['inline','off']){
   const disabled={...s,modes:{...s.modes,characters:mode}};
   assert.equal(validateDraft(formatExample(s),source,disabled)[0].details.characters,undefined);
   assert.equal(summarySchema(disabled).properties.memories.items.properties.details.properties.characters,undefined);
  }
 }
 assert.deepEqual(summarySchema(DEFAULTS).properties.memories.items.properties.details.properties.characters,{type:'string'});
});
test('every stage and prompt variant includes concise evidence-based character constraints',()=>{
 for(const promptVariant of ['original','extended','custom'])for(const level of [1,2,3]){
  const prompt=summaryPrompt({...DEFAULTS,promptVariant},'',level);
  for(const rule of ['每人至多一句','char、user 和 NPC','不重复角色卡','不猜测、不编造','details.characters'])assert.ok(prompt.includes(rule),rule);
 }
});
test('settings show character choices and a labeled closed escaped output example',()=>{
 const view=settingsView({...structuredClone(DEFAULTS),outputMode:'tags'},[],'',[]);
 assert.ok(view.includes('data-mode="characters"'));assert.ok(view.includes('data-send="characters"'));
 assert.match(view,/<details class="smm-help" ><summary>.*?输出格式示例（仅供查看，不是报错）/s);
 assert.ok(view.includes('<pre data-output-example>&lt;stm4-record&gt;'));
 assert.ok(!view.includes('<stm4-record>'));
});

test('legacy archives receive the new field without replacing existing selections',()=>{
 const s={...structuredClone(DEFAULTS),modes:{time:'off'},sendFields:{time:false}};
 const view=settingsView(s,[],'',[]);
 assert.match(view,/data-mode="characters">.*?<option value="separate" selected>/s);
 assert.match(view,/data-mode="time">.*?<option value="off" selected>/s);
 assert.match(view,/data-send="characters" checked/);
});
