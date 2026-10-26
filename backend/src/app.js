import express from "express";
import helmet from "helmet";
import cors from "cors";
import rateLimit from "express-rate-limit";
import { ZodError } from "zod";
import auth from "./routes/auth.js";
import events from "./routes/events.js";
import alerts from "./routes/alerts.js";
import settings from "./routes/settings.js";
import stats from "./routes/stats.js";
import vault from "./routes/vault.js";
export function createApp(config, io = { emit() {} }) {
  const app = express();
  app.disable("x-powered-by");
  app.use(
    helmet(),
    cors({ origin: config.origin }),
    express.json({ limit: "2mb" }),
    rateLimit({ windowMs: 60000, limit: 1000 }),
  );
  app.get("/api/health", (req, res) => res.json({ status: "ok" }));
  for (const [name, router] of Object.entries({
    auth: auth(config),
    events: events(config, io),
    alerts: alerts(config, io),
    settings: settings(config, io),
    stats: stats(config),
    vault: vault(config),
  }))
    app.use("/api/" + name, router);
  app.use((req, res) => res.status(404).json({ error: "Not found" }));
  app.use((error, req, res, _next) => {
    if (error instanceof ZodError)
      return res
        .status(400)
        .json({ error: "Invalid input", fields: error.flatten() });
    if (error.code === "LIMIT_FILE_SIZE")
      return res.status(413).json({ error: "File exceeds 50 MB" });
    if (error.name === "MulterError" || error.type === "entity.parse.failed")
      return res.status(400).json({ error: "Invalid request" });
    res.status(500).json({ error: "Internal server error" });
  });
  return app;
}
