import { Router } from "express";
import rateLimit from "express-rate-limit";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import Admin from "../models/Admin.js";
import { validate } from "../middleware/validate.js";
import { loginSchema } from "../schemas.js";
export default (config) => {
  const router = Router();
  router.post(
    "/login",
    rateLimit({ windowMs: 60000, limit: 10 }),
    validate(loginSchema),
    async (req, res) => {
      const admin = await Admin.findOne({ username: req.body.username });
      if (
        !admin ||
        !(await bcrypt.compare(req.body.password, admin.passwordHash))
      )
        return res.status(401).json({ error: "Invalid credentials" });
      res.json({
        token: jwt.sign({ role: "admin" }, config.jwtSecret, {
          subject: admin.id,
          expiresIn: "8h",
          issuer: "argus",
          audience: "argus-admin",
          algorithm: "HS256",
        }),
      });
    },
  );
  return router;
};
