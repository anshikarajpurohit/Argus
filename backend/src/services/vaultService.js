import { randomBytes, scrypt as scryptCallback, createCipheriv, createDecipheriv, createHash } from 'node:crypto';
import { promisify } from 'node:util';
const scrypt=promisify(scryptCallback);
const derive=(password,salt)=>scrypt(password,salt,32,{N:32768,r:8,p:1,maxmem:64*1024*1024});
export const hash=buffer=>createHash('sha256').update(buffer).digest('hex');
export async function encrypt(plaintext,password) {
 const salt=randomBytes(16),iv=randomBytes(12),key=await derive(password,salt);
 try{const cipher=createCipheriv('aes-256-gcm',key,iv);const content=Buffer.concat([cipher.update(plaintext),cipher.final()]);return Buffer.concat([Buffer.from('MEDR1'),salt,iv,cipher.getAuthTag(),content]);}finally{key.fill(0);}
}
export async function decrypt(stored,password) {
 if(stored.length<49 || stored.subarray(0,5).toString()!=='MEDR1') throw new Error('Decryption failed');
 const key=await derive(password,stored.subarray(5,21));
 try{const cipher=createDecipheriv('aes-256-gcm',key,stored.subarray(21,33));cipher.setAuthTag(stored.subarray(33,49));return Buffer.concat([cipher.update(stored.subarray(49)),cipher.final()]);}finally{key.fill(0);}
}
