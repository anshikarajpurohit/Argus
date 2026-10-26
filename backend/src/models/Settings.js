import mongoose from "mongoose";
export default mongoose.model(
  "Settings",
  new mongoose.Schema(
    {
      _id: { type: String, default: "singleton" },
      responseMode: { type: String, default: "alert_only" },
      warningThreshold: { type: Number, default: 40 },
      criticalThreshold: { type: Number, default: 70 },
      processAllowlist: {
        type: [String],
        default: [
          "explorer.exe",
          "systemd",
          "python",
          "node",
          "mongod",
          "code",
          "chrome",
          "firefox",
        ],
      },
    },
    { versionKey: false },
  ),
);
