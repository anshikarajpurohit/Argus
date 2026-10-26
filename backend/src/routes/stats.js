import { Router } from "express";
import Event from "../models/Event.js";
import Alert from "../models/Alert.js";
import { adminAuth } from "../middleware/adminAuth.js";
export default (config) => {
  const router = Router();
  router.use(adminAuth(config));
  router.get("/summary", async (req, res) => {
    const since = Date.now() / 1000 - 86400;
    const [eventsLast24h, alertsOpen, alertsCritical24h, files] =
      await Promise.all([
        Event.countDocuments({ ts: { $gte: since } }),
        Alert.countDocuments({ status: "open" }),
        Alert.countDocuments({ ts: { $gte: since }, severity: "CRITICAL" }),
        Alert.aggregate([
          { $match: { ts: { $gte: since } } },
          { $unwind: "$affectedFiles" },
          { $group: { _id: "$affectedFiles" } },
          { $count: "count" },
        ]),
      ]);
    res.json({
      eventsLast24h,
      alertsOpen,
      alertsCritical24h,
      filesAffected24h: files[0]?.count || 0,
    });
  });
  router.get("/timeline", async (req, res) => {
    const end = Math.floor(Date.now() / 60000) * 60,
      start = end - 59 * 60;
    const aggregate = (model) =>
      model.aggregate([
        { $match: { ts: { $gte: start, $lt: end + 60 } } },
        {
          $group: {
            _id: { $multiply: [{ $floor: { $divide: ["$ts", 60] } }, 60] },
            count: { $sum: 1 },
          },
        },
      ]);
    const [events, alerts] = await Promise.all([
      aggregate(Event),
      aggregate(Alert),
    ]);
    const e = new Map(events.map((x) => [x._id, x.count])),
      a = new Map(alerts.map((x) => [x._id, x.count]));
    res.json(
      Array.from({ length: 60 }, (_, i) => ({
        ts: start + i * 60,
        events: e.get(start + i * 60) || 0,
        alerts: a.get(start + i * 60) || 0,
      })),
    );
  });
  return router;
};
