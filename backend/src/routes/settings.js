import { Router } from 'express';
import Settings from '../models/Settings.js';
import { settingsSchema } from '../schemas.js';
import { validate } from '../middleware/validate.js';
import { validAgentKey } from '../middleware/agentAuth.js';
import { adminAuth } from '../middleware/adminAuth.js';
export default(config,io)=>{const router=Router();router.get('/',(req,res,next)=>validAgentKey(req.headers['x-agent-key'],config)?next():adminAuth(config)(req,res,next),async(req,res)=>res.json(await Settings.findById('singleton').select('-_id').lean()));router.put('/',adminAuth(config),validate(settingsSchema),async(req,res)=>{const settings=await Settings.findByIdAndUpdate('singleton',req.body,{new:true,upsert:true}).select('-_id');io.emit('settings:updated',settings);res.json(settings);});return router;};
