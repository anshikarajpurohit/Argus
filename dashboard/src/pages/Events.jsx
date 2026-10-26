import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { api, getToken, setToken, message } from '../api';
import { Badge, ErrorBox, Empty, Title, AlertTable, time } from '../components/common';
import { useData } from '../hooks/useData';
import { securityStatus, byteSize } from '../helpers';
export default function Events({ refresh }) {
  const [action, A] = useState(""),
    [canary, C] = useState(""),
    [from, F] = useState(""),
    [to, T] = useState("");
  const query = new URLSearchParams({ limit: "100" });
  if (action) query.set("action", action);
  if (canary) query.set("isCanary", canary);
  if (from) query.set("from", String(new Date(from).getTime() / 1000));
  if (to) query.set("to", String(new Date(to).getTime() / 1000));
  const { data, error } = useData("/events?" + query, refresh);
  return (
    <main>
      <Title
        eyebrow="FILESYSTEM TELEMETRY"
        title="Events"
        description="Inspect recent file changes across monitored folders."
      />
      <div className="filters">
        <label>
          Action
          <select value={action} onChange={(e) => A(e.target.value)}>
            <option value="">All actions</option>
            {["created", "modified", "deleted", "moved"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label>
          Canary
          <select value={canary} onChange={(e) => C(e.target.value)}>
            <option value="">All files</option>
            <option value="true">Canaries only</option>
            <option value="false">Regular files</option>
          </select>
        </label>
        <label>
          From
          <input
            type="datetime-local"
            value={from}
            onChange={(e) => F(e.target.value)}
          />
        </label>
        <label>
          To
          <input
            type="datetime-local"
            value={to}
            onChange={(e) => T(e.target.value)}
          />
        </label>
      </div>
      <ErrorBox error={error} />
      <section className="panel">
        {data?.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {[
                    "Time",
                    "Action",
                    "File path",
                    "Entropy",
                    "Size",
                    "Canary",
                  ].map((x) => (
                    <th key={x}>{x}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((e) => (
                  <tr key={e.eventId}>
                    <td>{time(e.ts)}</td>
                    <td>
                      <Badge value={e.action} />
                    </td>
                    <td className="path-cell">
                      {e.path}
                      {e.destPath && <small>→ {e.destPath}</small>}
                    </td>
                    <td>{e.entropy?.toFixed(2) ?? "—"}</td>
                    <td>
                      {e.sizeBytes === null ? "—" : byteSize(e.sizeBytes)}
                    </td>
                    <td>{e.isCanary ? "Tripwire" : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty />
        )}
      </section>
      <p className="footnote">
        Showing the latest 100 matching events. Event records expire after seven
        days.
      </p>
    </main>
  );
}
