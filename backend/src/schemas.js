import { z } from 'zod';
const nullableNumber = z.number().finite().nonnegative().nullable();
const nullableText = z.string().max(4096).nullable();
export const eventSchema = z.object({
  eventId: z.uuid(), agentId: z.string().min(1).max(128), ts: z.number().finite().nonnegative(),
  action: z.enum(['created','modified','deleted','moved']), path: z.string().min(1).max(4096), destPath: nullableText,
  ext: z.string().max(128), destExt: z.string().max(128).nullable(), sizeBytes: nullableNumber,
  entropy: z.number().min(0).max(8).nullable(), prevEntropy: z.number().min(0).max(8).nullable(),
  isCanary: z.boolean(), suspectPid: z.number().int().nonnegative().nullable(), suspectProcess: nullableText
}).strict();
export const alertSchema = z.object({
  alertId: z.uuid(), agentId: z.string().min(1).max(128), ts: z.number().finite().nonnegative(),
  severity: z.enum(['WARNING','CRITICAL']), score: z.number().min(0).max(100), reasons: z.array(z.string().max(128)).max(30),
  mlProbability: z.number().min(0).max(1).nullable(), affectedFiles: z.array(z.string().max(4096)).max(50),
  suspectPid: z.number().int().nonnegative().nullable(), suspectProcess: nullableText,
  responseTaken: z.enum(['none','suspended','suspend_failed']), status: z.enum(['open','acknowledged','resolved']).default('open')
}).strict();
export const settingsSchema = z.object({ responseMode: z.enum(['alert_only','suspend']), warningThreshold: z.number().min(0).max(100), criticalThreshold: z.number().min(0).max(100), processAllowlist: z.array(z.string().min(1).max(256)).max(200) }).strict().refine(v => v.warningThreshold < v.criticalThreshold, {message:'warningThreshold must be below criticalThreshold',path:['warningThreshold']});
export const statusSchema = z.object({status: z.enum(['open','acknowledged','resolved'])}).strict();
export const loginSchema = z.object({username:z.string().min(1).max(128),password:z.string().min(1).max(1024)}).strict();
export const passwordSchema = z.object({password:z.string().min(1).max(1024)}).strict();
export const querySchema = z.object({limit:z.coerce.number().int().min(1).max(500).default(100),action:z.enum(['created','modified','deleted','moved']).optional(),isCanary:z.enum(['true','false']).optional(),from:z.coerce.number().finite().nonnegative().optional(),to:z.coerce.number().finite().nonnegative().optional(),status:z.enum(['open','acknowledged','resolved']).optional(),severity:z.enum(['WARNING','CRITICAL']).optional()}).strict();
