import {describe,it,expect} from 'vitest';
import {securityStatus,mergeAlert,byteSize} from './helpers';
describe('dashboard state',()=>{
 it('ignores stale and resolved alerts',()=>expect(securityStatus([{ts:1,severity:'CRITICAL',status:'open'},{ts:999,severity:'CRITICAL',status:'resolved'}],1000)).toBe('Normal'));
 it('uses newest open alert',()=>expect(securityStatus([{ts:999,severity:'WARNING',status:'open'},{ts:998,severity:'CRITICAL',status:'open'}],1000)).toBe('Warning'));
 it('deduplicates status updates',()=>expect(mergeAlert([{alertId:'a',ts:1}],{alertId:'a',ts:1,status:'resolved'})).toHaveLength(1));
 it('formats file sizes',()=>{expect(byteSize(1024)).toBe('1.0 KB');expect(byteSize(1)).toBe('1 B');});
});
