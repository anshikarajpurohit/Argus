import React, { useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import {
  Badge,
  ErrorBox,
  Empty,
  Title,
  AlertTable,
} from "../components/common";
import { useData } from "../hooks/useData";
import { securityStatus } from "../helpers";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { time } from "../components/common";
export default function Overview({ refresh }) {
  const summary = useData("/stats/summary", refresh),
    timeline = useData("/stats/timeline", refresh),
    alerts = useData("/alerts?limit=20", refresh);
  const [now, N] = useState(Date.now() / 1000);
  useEffect(() => {
    const id = setInterval(() => N(Date.now() / 1000), 10000);
    return () => clearInterval(id);
  }, []);
  const status = securityStatus(alerts.data || [], now);
  return (
    <main>
      <Title
        eyebrow="AT A GLANCE"
        title="Security overview"
        description="Your endpoint activity, with the signal brought forward."
      >
        <Badge value={alerts.data ? status : "Loading"} />
      </Title>
      <ErrorBox error={summary.error || timeline.error || alerts.error} />
      <div className="metrics">
        {[
          ["Events, last 24h", "eventsLast24h", "≋"],
          ["Open alerts", "alertsOpen", "◇"],
          ["Critical, last 24h", "alertsCritical24h", "△"],
          ["Affected files, last 24h", "filesAffected24h", "▤"],
        ].map(([label, key, icon]) => (
          <section className="metric" key={key}>
            <span>
              {label}
              <i>{icon}</i>
            </span>
            <strong>{summary.data?.[key]?.toLocaleString() ?? "—"}</strong>
            <small>
              {key === "eventsLast24h"
                ? "Filesystem activity"
                : "Detection summary"}
            </small>
          </section>
        ))}
      </div>
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Activity timeline</h2>
            <p>Events and alerts · last 60 minutes</p>
          </div>
          <div className="legend">
            <span>● Events</span>
            <span>● Alerts</span>
          </div>
        </div>
        <div className="chart">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={timeline.data || []}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="#e9edf2"
              />
              <XAxis
                dataKey="ts"
                tickFormatter={(t) =>
                  new Date(t * 1000).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                }
                minTickGap={50}
                tick={{ fontSize: 11 }}
              />
              <YAxis tick={{ fontSize: 11 }} width={40} />
              <Tooltip labelFormatter={time} />
              <Line
                type="monotone"
                dataKey="events"
                stroke="#3b8177"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="alerts"
                stroke="#d76853"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Recent alerts</h2>
            <p>Updated live as detections arrive</p>
          </div>
          <NavLink to="/alerts">View all alerts →</NavLink>
        </div>
        {alerts.data?.length ? (
          <AlertTable items={alerts.data.slice(0, 6)} />
        ) : (
          <Empty text="No alerts to review" />
        )}
      </section>
      <p className="footnote">
        Detection is heuristic. Process attribution is best-effort; synthetic
        model performance does not establish real-world accuracy.
      </p>
    </main>
  );
}
