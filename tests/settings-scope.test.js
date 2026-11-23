import test from 'node:test';
import assert from 'node:assert/strict';
import {migrateSharedSettings,chatProgress,SHARED_SETTINGS_SCOPE} from '../settings-scope.js';

test('upgrade adopts active chat preferences once without copying cursors or connection fields',()=>{
 const defaults={detail:'standard',check:true,startFloor:0,autoStartFloor:0,baseUrl:'',worldBooks:[],modes:{time:'off'}};
 const global={baseUrl:'https://example.invalid',detail:'standard'};
 const saved={settingsSchema:2,detail:'detailed',check:false,startFloor:51,autoStartFloor:51,baseUrl:'obsolete',modes:{time:'separate'}};
 assert.equal(migrateSharedSettings(global,saved,defaults,new Set(['baseUrl']),2),true);
 assert.deepEqual(global,{baseUrl:'https://example.invalid',detail:'detailed',check:false,modes:{time:'separate'},settingsScope:SHARED_SETTINGS_SCOPE});
 saved.modes.time='off';assert.equal(global.modes.time,'separate');
 assert.equal(migrateSharedSettings(global,{...saved,detail:'other chat'},defaults,new Set(['baseUrl']),2),false);
 assert.equal(global.detail,'detailed');
});

test('invalid legacy options cannot override shared defaults, and empty book selection stays empty',()=>{
 const global={detail:'standard',worldBooks:[]};
 migrateSharedSettings(global,{settingsSchema:1,detail:'bad'}, {detail:'standard'},new Set(),2);
 assert.equal(global.detail,'standard');
 migrateSharedSettings(global,null,{},new Set(),2);
 assert.deepEqual(global.worldBooks,[]);
});

test('only progress is written per chat, and new chats never inherit another chat cursor',()=>{
 assert.deepEqual(chatProgress({startFloor:51,autoStartFloor:53,detail:'detailed',apiKey:'never copy'},2),{settingsSchema:2,startFloor:51,autoStartFloor:53});
 assert.deepEqual(chatProgress(undefined,2),{settingsSchema:2,startFloor:0,autoStartFloor:0});
});
