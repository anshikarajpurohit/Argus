import { timingSafeEqual } from 'node:crypto';
export function validAgentKey(value,config) {
 if(typeof value !== 'string') return false;
 const a=Buffer.from(value),b=Buffer.from(config.agentKey);
 return a.length === b.length && timingSafeEqual(a,b);
}
export const agentAuth = config => (req,res,next) => validAgentKey(req.headers['x-agent-key'],config) ? next() : res.status(401).json({error:'Unauthorized'});
