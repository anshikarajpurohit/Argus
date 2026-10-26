import { Router } from 'express';
import Alert from '../models/Alert.js';
import { alertSchema,statusSchema,querySchema } from '../schemas.js';
import { validate } from '../middleware/validate.js';
import { agentAuth } from '../middleware/agentAuth.js';
import { adminAuth } from '../middleware/adminAuth.js';
export default(config,io)=>{const router=Router();router.post('/',agentAuth(config),validate(alertSchema),async(req,res)=>{
 const result=await Alert.updateOne({alertId:req.body.alertId},{$setOnInsert:req.body},{upsert:true});
 if(result.upsertedCount)io.emit('alert:new',req.body);res.status(201).json(req.body);
});router.get('/',adminAuth(config),async(req,res)=>{const q=querySchema.parse(req.query),filter={};if(q.status)filter.status=q.status;if(q.severity)filter.severity=q.severity;res.json(await Alert.find(filter).select('-_id').sort({ts:-1}).limit(q.limit).lean());});
 router.patch('/:alertId',adminAuth(config),validate(statusSchema),async(req,res)=>{const item=await Alert.findOneAndUpdate({alertId:req.params.alertId},req.body,{new:true}).select('-_id');if(!item)return res.status(404).json({error:'Not found'});io.emit('alert:new',item);res.json(item);});return router;};
