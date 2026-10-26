export const validate = schema => (req,res,next) => {
 const result=schema.safeParse(req.body);
 if(!result.success) return res.status(400).json({error:'Invalid input',fields:result.error.flatten()});
 req.body=result.data; next();
};
