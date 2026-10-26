import { beforeAll, afterAll, test, expect } from "@jest/globals";
import mongoose from "mongoose";
import bcrypt from "bcryptjs";
import request from "supertest";
import { randomUUID } from "node:crypto";
import { mkdtemp, rm, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createServer } from "node:http";
import { io as client } from "socket.io-client";
import { createApp } from "../src/app.js";
import { createSocket } from "../src/services/socket.js";
import { loadConfig } from "../src/config.js";
import Admin from "../src/models/Admin.js";
import Event from "../src/models/Event.js";
import Alert from "../src/models/Alert.js";
import Settings from "../src/models/Settings.js";
import VaultItem from "../src/models/VaultItem.js";
let app, token, config, directory;
const db = "argus_test_" + randomUUID().replaceAll("-", "");
const event = () => ({
  eventId: randomUUID(),
  agentId: "test",
  ts: Date.now() / 1000,
  action: "modified",
  path: "/test/a.txt",
  destPath: null,
  ext: ".txt",
  destExt: null,
  sizeBytes: 1000,
  entropy: 4.2,
  prevEntropy: 4.1,
  isCanary: false,
  suspectPid: null,
  suspectProcess: null,
});
const auth = () => ({ Authorization: "Bearer " + token });
beforeAll(async () => {
  directory = await mkdtemp(join(tmpdir(), "argus-vault-test-"));
  config = {
    jwtSecret: "random-test-only-secret-value-at-least-32-characters",
    agentKey: "test-agent-key",
    origin: "http://localhost:5173",
    vaultDir: directory,
  };
  await mongoose.connect(
    process.env.MONGO_TEST_URI || "mongodb://127.0.0.1:27028/",
    { dbName: db, serverSelectionTimeoutMS: 5000 },
  );
  await Promise.all([
    Admin.init(),
    Event.init(),
    Alert.init(),
    VaultItem.init(),
  ]);
  await Admin.create({
    username: "admin",
    passwordHash: await bcrypt.hash("test-password", 10),
  });
  await Settings.create({ _id: "singleton" });
  app = createApp(config);
  token = (
    await request(app)
      .post("/api/auth/login")
      .send({ username: "admin", password: "test-password" })
  ).body.token;
}, 30000);
afterAll(async () => {
  if (mongoose.connection.readyState === 1)
    await mongoose.connection.dropDatabase();
  await mongoose.disconnect();
  await rm(directory, { recursive: true, force: true });
});
test("configuration rejects placeholder secrets", () => {
  expect(() =>
    loadConfig({ JWT_SECRET: "short", AGENT_API_KEY: "x" }),
  ).toThrow();
  expect(() =>
    loadConfig({ JWT_SECRET: "a".repeat(40), AGENT_API_KEY: "CHANGE_ME" }),
  ).toThrow();
});
test("health, login success/failure, protected endpoints", async () => {
  expect(token).toBeTruthy();
  expect((await request(app).get("/api/health")).status).toBe(200);
  expect(
    (
      await request(app)
        .post("/api/auth/login")
        .send({ username: "admin", password: "wrong" })
    ).status,
  ).toBe(401);
  for (const url of [
    "/api/events",
    "/api/alerts",
    "/api/stats/summary",
    "/api/settings",
    "/api/vault",
  ])
    expect((await request(app).get(url)).status).toBe(401);
  expect(
    (
      await request(app)
        .post("/api/events/batch")
        .set("x-agent-key", "wrong")
        .send({ events: [event()] })
    ).status,
  ).toBe(401);
});
test("200-event batches, 201 rejection, validation and idempotency", async () => {
  const events = Array.from({ length: 200 }, event);
  const post = (events) =>
    request(app)
      .post("/api/events/batch")
      .set("x-agent-key", config.agentKey)
      .send({ events });
  expect((await post(events)).status).toBe(201);
  expect((await post(events)).body.count).toBe(0);
  expect((await post([...events, event()])).status).toBe(400);
  expect((await post([{ ...event(), entropy: 9 }])).status).toBe(400);
  expect(await Event.countDocuments()).toBe(200);
  const stored = await Event.findOne();
  expect(stored.expiresAt).toBeInstanceOf(Date);
  expect(
    (await request(app).get("/api/events?isCanary=nonsense").set(auth()))
      .status,
  ).toBe(400);
});
test("settings persist and validate threshold ordering", async () => {
  const data = {
    responseMode: "alert_only",
    warningThreshold: 40,
    criticalThreshold: 70,
    processAllowlist: ["node"],
  };
  expect(
    (
      await request(app)
        .put("/api/settings")
        .set(auth())
        .send({ ...data, warningThreshold: 80 })
    ).status,
  ).toBe(400);
  expect(
    (await request(app).put("/api/settings").set(auth()).send(data)).status,
  ).toBe(200);
  expect(
    (
      await request(app)
        .get("/api/settings")
        .set("x-agent-key", config.agentKey)
    ).body.responseMode,
  ).toBe("alert_only");
});
test("alert lifecycle, statistics, timeline", async () => {
  const alert = {
    alertId: randomUUID(),
    agentId: "test",
    ts: Date.now() / 1000,
    severity: "CRITICAL",
    score: 100,
    reasons: ["canary_touched"],
    mlProbability: null,
    affectedFiles: ["/test/a.txt"],
    suspectPid: null,
    suspectProcess: null,
    responseTaken: "none",
    status: "open",
  };
  expect(
    (
      await request(app)
        .post("/api/alerts")
        .set("x-agent-key", config.agentKey)
        .send(alert)
    ).status,
  ).toBe(201);
  expect(
    (await request(app).get("/api/alerts?severity=CRITICAL").set(auth())).body,
  ).toHaveLength(1);
  const stats = (await request(app).get("/api/stats/summary").set(auth())).body;
  expect(stats.alertsOpen).toBe(1);
  expect(stats.filesAffected24h).toBe(1);
  expect(
    (await request(app).get("/api/stats/timeline").set(auth())).body,
  ).toHaveLength(60);
  expect(
    (
      await request(app)
        .patch("/api/alerts/" + alert.alertId)
        .set(auth())
        .send({ status: "resolved" })
    ).body.status,
  ).toBe("resolved");
});
test("vault round-trip, randomized ciphertext, bad password, tamper, delete", async () => {
  const plain = Buffer.from("An explicit user-submitted private document.");
  const upload = () =>
    request(app)
      .post("/api/vault/upload")
      .set(auth())
      .field("password", "test-vault-password")
      .attach("file", plain, "notes.txt");
  const a = await upload(),
    b = await upload();
  expect(a.status).toBe(201);
  expect(b.status).toBe(201);
  const bytes = await readFile(join(directory, a.body.storedName));
  expect(bytes.subarray(0, 5).toString()).toBe("MEDR1");
  expect(bytes.equals(await readFile(join(directory, b.body.storedName)))).toBe(
    false,
  );
  const download = await request(app)
    .post("/api/vault/" + a.body.itemId + "/decrypt")
    .set(auth())
    .send({ password: "test-vault-password" });
  expect(download.status).toBe(200);
  expect(Buffer.from(download.text || download.body).equals(plain)).toBe(true);
  expect(
    (
      await request(app)
        .post("/api/vault/" + a.body.itemId + "/decrypt")
        .set(auth())
        .send({ password: "wrong" })
    ).status,
  ).toBe(403);
  bytes[bytes.length - 1] ^= 1;
  await writeFile(join(directory, a.body.storedName), bytes);
  expect(
    (
      await request(app)
        .post("/api/vault/" + a.body.itemId + "/decrypt")
        .set(auth())
        .send({ password: "test-vault-password" })
    ).status,
  ).toBe(403);
  expect(
    (
      await request(app)
        .delete("/api/vault/" + a.body.itemId)
        .set(auth())
    ).status,
  ).toBe(204);
}, 20000);
test("oversize vault upload rejected", async () => {
  const response = await request(app)
    .post("/api/vault/upload")
    .set(auth())
    .field("password", "test")
    .attach("file", Buffer.alloc(50 * 1024 * 1024 + 1), "large.bin");
  expect(response.status).toBe(413);
}, 20000);
test("Socket.IO rejects missing JWT and accepts valid JWT", async () => {
  const server = createServer(createApp(config));
  const io = createSocket(server, config);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const url = "http://127.0.0.1:" + server.address().port;
  try {
    await new Promise((resolve, reject) => {
      const socket = client(url, { reconnection: false, timeout: 2000 });
      socket.on("connect_error", () => {
        socket.disconnect();
        resolve();
      });
      socket.on("connect", () => {
        socket.disconnect();
        reject(new Error("Unauthenticated connection accepted"));
      });
    });
    await new Promise((resolve, reject) => {
      const socket = client(url, {
        auth: { token },
        reconnection: false,
        timeout: 2000,
      });
      socket.on("connect", () => {
        socket.disconnect();
        resolve();
      });
      socket.on("connect_error", (e) => {
        socket.disconnect();
        reject(e);
      });
    });
  } finally {
    await new Promise((resolve) => io.close(resolve));
  }
});
