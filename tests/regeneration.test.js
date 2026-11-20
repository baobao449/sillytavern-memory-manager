
import test from 'node:test';
import assert from 'node:assert/strict';
import {DEFAULTS,sourceSnapshot} from '../core.js';
import {buildSummaryMessages} from '../summary-request.js';
import {compactReviewNotes,mapReviewedRewrite} from '../memory-tools.js';
import {mergeCandidates,automaticMerge} from '../summary-rules.js';

test('rewrite avoids duplicated instructions, raw review metadata and previous draft while preserving complete source',()=>{
 const issues=[{id:'internal',message:'核对日期',suggestion:'勿推断日期',field:'details.time',quote:'明日',location:'private-location'}];
 const reviewNotes=compactReviewNotes([...issues,...issues]);
 assert.equal(reviewNotes.length,1);
 assert.ok(!JSON.stringify(reviewNotes).includes('internal'));
 const source='剧情材料'.repeat(60000);
 for(const outputMode of ['json','tags','plain']){
  const sources=[{floor:20,role:'assistant',text:source,raw:'LOCAL_RAW'}];
  const refs={worldBooks:[],memories:[],character:null};
  const initial=buildSummaryMessages({...DEFAULTS,outputMode},sources,refs);
  const rewritten=buildSummaryMessages({...DEFAULTS,outputMode},sources,refs,'',false,1,{userInstruction:'合成一条，以原文明示时间为准',reviewNotes});
  const payload=JSON.parse(rewritten[1].content);
  assert.equal(payload.sources[0].text,source);
  assert.equal(payload.task.requirements,undefined);
  assert.equal(payload.task.revision.userInstruction,'合成一条，以原文明示时间为准');
  assert.equal(payload.outputContract.format,outputMode);
  assert.ok(rewritten[0].content.includes('以用户要求为准'));
  assert.ok(rewritten[1].content.length<initial[1].content.length);
  assert.ok(!rewritten[1].content.includes('LOCAL_RAW'));
 }
});
test('same materials: tag casing and one-sided whitelist preserve body; blacklist excludes thinking',()=>{
 const body='阿宁与众人完成同一场对峙。'.repeat(5000);
 const settings={...DEFAULTS,sourceTag:'content,context',excludeTags:'think,thinking,details,summary'};
 for(const mes of ['<content>'+body+'</content>','<CONTENT>'+body+'</CONTENT>','<CONTENT>'+body]){
  assert.equal(sourceSnapshot([{mes}],0,0,settings)[0].text,body);
 }
 assert.equal(sourceSnapshot([{mes:'<think>内部思考</think><CONTENT>'+body+'</CONTENT>'}],0,0,settings)[0].text,body);
});
test('organization and automatic thresholds share eligibility after merge, fixed, imported, and reservations',()=>{
 const memories=Array.from({length:10},(_,i)=>({id:String(i),level:1,status:'active',kind:'short',sources:[i]}));
 assert.equal(mergeCandidates(memories,1).length,10);
 memories.slice(0,5).forEach(m=>m.status='archived');
 assert.equal(mergeCandidates(memories,1).length,5);
 assert.equal(automaticMerge(memories,[],{autoSecondary:true,secondaryCount:5}).parents.length,5);
 assert.equal(mergeCandidates(memories,1,new Set(['5'])).length,4);
 memories[5].kind='fixed';memories[6].imported=true;memories[7].sources=[];
 assert.equal(mergeCandidates(memories,1).length,2);
 assert.equal(automaticMerge(memories,[],{autoSecondary:true,secondaryCount:5}),null);
});

test('saved rewrite matches by unique source rather than positional index and never overwrites ambiguous records',()=>{
 const previous=[{id:'one',sources:[1],kind:'short',summary:'old1'},{id:'two',sources:[2],kind:'long',summary:'old2'}];
 const next=[{sources:[2],summary:'new2',keywords:[]},{sources:[1],summary:'new1',keywords:[]}];
 const mapped=mapReviewedRewrite(previous,next);
 assert.equal(mapped[0].id,'two');assert.equal(mapped[0].kind,'long');
 assert.equal(mapped[1].id,'one');
 assert.equal(previous[0].summary,'old1');
 assert.throws(()=>mapReviewedRewrite(previous,[next[0]]),/条数/);
 assert.throws(()=>mapReviewedRewrite([{...previous[0],sources:[1]},{...previous[1],sources:[1]}],[{sources:[1]},{sources:[1]}]),/唯一/);
});
