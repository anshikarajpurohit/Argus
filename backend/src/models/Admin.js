import mongoose from "mongoose";
export default mongoose.model(
  "Admin",
  new mongoose.Schema(
    { username: { type: String, unique: true }, passwordHash: String },
    { versionKey: false },
  ),
);
