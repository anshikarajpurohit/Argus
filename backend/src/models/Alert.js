import mongoose from 'mongoose';
export default mongoose.model('Alert',new mongoose.Schema({alertId:{type:String,unique:true},agentId:String,ts:{type:Number,index:true},severity:String,score:Number,reasons:[String],mlProbability:Number,affectedFiles:[String],suspectPid:Number,suspectProcess:String,responseTaken:String,status:{type:String,default:'open',index:true}},{versionKey:false}));
