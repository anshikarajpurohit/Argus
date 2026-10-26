import { Server } from 'socket.io';
import { verifyToken } from '../middleware/adminAuth.js';
export function createSocket(server,config) {
 const io=new Server(server,{cors:{origin:config.origin}});
 io.use((socket,next)=>{try{const claims=verifyToken(socket.handshake.auth?.token,config);socket.data.expires=claims.exp*1000;next();}catch{next(new Error('Unauthorized'));}});
 io.on('connection',socket=>{const timer=setTimeout(()=>socket.disconnect(true),Math.max(0,socket.data.expires-Date.now()));socket.on('disconnect',()=>clearTimeout(timer));});
 return io;
}
