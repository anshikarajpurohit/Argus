import { createServer } from 'node:http';
import mongoose from 'mongoose';
import { loadConfig } from './config.js';
import { createApp } from './app.js';
import { createSocket } from './services/socket.js';
import Settings from './models/Settings.js';
const config=loadConfig();await mongoose.connect(config.mongoUri);await Settings.updateOne({_id:'singleton'},{$setOnInsert:{_id:'singleton'}},{upsert:true});
const server=createServer();const io=createSocket(server,config);server.on('request',createApp(config,io));server.listen(config.port,'127.0.0.1',()=>console.log(`Argus API on http://127.0.0.1:${config.port}`));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>io.close(()=>server.close(async()=>{await mongoose.disconnect();process.exit(0);}))); 
