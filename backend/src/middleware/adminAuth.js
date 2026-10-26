import jwt from 'jsonwebtoken';
export function verifyToken(token, config) {
 const payload=jwt.verify(token,config.jwtSecret,{algorithms:['HS256'],issuer:'argus',audience:'argus-admin'});
 if(payload.role !== 'admin') throw new Error('Unauthorized');
 return payload;
}
export const adminAuth = config => (req,res,next) => {
 try {req.admin=verifyToken(req.headers.authorization?.replace(/^Bearer /,''),config);next();}
 catch {res.status(401).json({error:'Unauthorized'});}
};
