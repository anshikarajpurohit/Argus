import { Router } from 'express';
import { z } from 'zod';
import Event from '../models/Event.js';
import { eventSchema,querySchema } from '../schemas.js';
import { validate } from '../middleware/validate.js';
import { agentAuth } from '../middleware/agentAuth.js';
import { adminAuth } from '../middleware/adminAuth.js';
export default(config,io)=>{const router=Router();router.post('/batch',agentAuth(config),validate(z.object({events:z.array(eventSchema).min(1).max(200)}).strict()),async(req,res)=>{
 const events=req.body.events;
 const result=await Event.bulkWrite(events.map(e=>({updateOne:{filter:{eventId:e.eventId},update:{$setOnInsert:{...e,expiresAt:new Date(e.ts*1000+7*86400000)}},upsert:true}})));
 io.emit('event:new',{count:result.upsertedCount,events:events.slice(-20)});res.status(201).json({count:result.upsertedCount});
});router.get('/',adminAuth(config),async(req,res)=>{
 const q=querySchema.parse(req.query),filter={};
 if(q.action)filter.action=q.action;if(q.isCanary)filter.isCanary=q.isCanary==='true';
 if(q.from!==undefined || q.to!==undefined){filter.ts={};if(q.from!==undefined)filter.ts.$gte=q.from;if(q.to!==undefined)filter.ts.$lte=q.to;}
 res.json(await Event.find(filter).select('-expiresAt -_id').sort({ts:-1}).limit(q.limit).lean());
});return router;};
