import mongoose from 'mongoose';
export default mongoose.model('VaultItem',new mongoose.Schema({itemId:{type:String,unique:true},originalName:String,storedName:String,sizeBytes:Number,createdAt:{type:Date,default:Date.now},sha256Plaintext:String},{versionKey:false}));
