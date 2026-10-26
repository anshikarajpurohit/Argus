import { Router } from 'express';
import multer from 'multer';
import { randomUUID } from 'node:crypto';
import { mkdir,writeFile,readFile,unlink } from 'node:fs/promises';
import { join,basename } from 'node:path';
import VaultItem from '../models/VaultItem.js';
import { adminAuth } from '../middleware/adminAuth.js';
import { validate } from '../middleware/validate.js';
import { passwordSchema } from '../schemas.js';
import { encrypt,decrypt,hash } from '../services/vaultService.js';
export default config=>{const router=Router();router.use(adminAuth(config));
 const upload=multer({storage:multer.memoryStorage(),limits:{fileSize:50*1024*1024,files:1,fields:1,fieldSize:4096}});
 router.post('/upload',upload.single('file'),validate(passwordSchema),async(req,res)=>{
 if(!req.file)return res.status(400).json({error:'A file is required'});
 const itemId=randomUUID(),storedName=itemId+'.vault',path=join(config.vaultDir,storedName);
 try{const sha256Plaintext=hash(req.file.buffer),encrypted=await encrypt(req.file.buffer,req.body.password);await mkdir(config.vaultDir,{recursive:true,mode:0o700});await writeFile(path,encrypted,{flag:'wx',mode:0o600});try{const item=await VaultItem.create({itemId,storedName,originalName:basename(req.file.originalname.replaceAll('\\','/')),sizeBytes:req.file.size,sha256Plaintext});res.status(201).json(item);}catch(error){await unlink(path);throw error;}}finally{req.file.buffer.fill(0);req.body.password='';}
 });
 router.get('/',async(req,res)=>res.json(await VaultItem.find().select('-_id').sort({createdAt:-1}).lean()));
 router.post('/:itemId/decrypt',validate(passwordSchema),async(req,res)=>{
 const item=await VaultItem.findOne({itemId:req.params.itemId});if(!item)return res.status(404).json({error:'Not found'});
 const stored=await readFile(join(config.vaultDir,item.storedName));let plain;
 try{plain=await decrypt(stored,req.body.password);}catch{return res.status(403).json({error:'Decryption failed'});}finally{req.body.password='';}
 if(hash(plain)!==item.sha256Plaintext){plain.fill(0);return res.status(500).json({error:'Integrity check failed'});}
 res.attachment(item.originalName);res.on('finish',()=>plain.fill(0));res.send(plain);
 });
 router.delete('/:itemId',async(req,res)=>{const item=await VaultItem.findOne({itemId:req.params.itemId});if(!item)return res.status(404).json({error:'Not found'});await unlink(join(config.vaultDir,item.storedName)).catch(error=>{if(error.code!=='ENOENT')throw error;});await item.deleteOne();res.status(204).end();});return router;};
