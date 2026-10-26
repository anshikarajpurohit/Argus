import mongoose from "mongoose";
import bcrypt from "bcryptjs";
import { loadConfig } from "./config.js";
import Admin from "./models/Admin.js";
const config = loadConfig();
if (
  !process.env.ADMIN_USER ||
  !process.env.ADMIN_PASS ||
  process.env.ADMIN_PASS.length < 12 ||
  process.env.ADMIN_PASS === "change_me_now"
)
  throw new Error("Set ADMIN_USER and ADMIN_PASS (12+ characters)");
await mongoose.connect(config.mongoUri);
await Admin.updateOne(
  { username: process.env.ADMIN_USER },
  { $set: { passwordHash: await bcrypt.hash(process.env.ADMIN_PASS, 12) } },
  { upsert: true },
);
await mongoose.disconnect();
console.log("Admin seeded");
