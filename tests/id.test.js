import test from 'node:test';
import assert from 'node:assert/strict';
import {newId} from '../core.js';

const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
test('newId preserves native UUID and survives missing Web Crypto',()=>{
 const descriptor=Object.getOwnPropertyDescriptor(globalThis,'crypto');
 try{
  Object.defineProperty(globalThis,'crypto',{configurable:true,value:{randomUUID:()=> 'native-id',getRandomValues:()=>{throw Error('fallback should not run');}}});
  assert.equal(newId(),'native-id');
  Object.defineProperty(globalThis,'crypto',{configurable:true,value:undefined});
  const first=newId(),second=newId();
  assert.match(first,uuid);assert.match(second,uuid);assert.notEqual(first,second);
 }finally{
  if(descriptor)Object.defineProperty(globalThis,'crypto',descriptor);else delete globalThis.crypto;
 }
});
