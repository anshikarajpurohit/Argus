import "dotenv/config";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
export function loadConfig(env = process.env) {
  if (
    !env.JWT_SECRET ||
    env.JWT_SECRET.length < 32 ||
    env.JWT_SECRET.startsWith("replace_")
  )
    throw new Error("Set a random JWT_SECRET of at least 32 characters");
  if (!env.AGENT_API_KEY || env.AGENT_API_KEY === "CHANGE_ME")
    throw new Error("Set AGENT_API_KEY");
  return {
    port: Number(env.PORT || 5000),
    mongoUri: env.MONGO_URI || "mongodb://127.0.0.1:27017/mini_edr",
    jwtSecret: env.JWT_SECRET,
    agentKey: env.AGENT_API_KEY,
    origin: env.CLIENT_ORIGIN || "http://localhost:5173",
    vaultDir: resolve(
      dirname(fileURLToPath(import.meta.url)),
      "../vault_store",
    ),
  };
}
