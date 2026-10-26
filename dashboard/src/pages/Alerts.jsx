import React, { useState } from "react";
import { api, message } from "../api";
import {
  Badge,
  ErrorBox,
  Empty,
  Title,
  AlertTable,
  time,
} from "../components/common";
import { useData } from "../hooks/useData";
export default function Alerts({ refresh }) {
  const [status, S] = useState(""),
    [severity, V] = useState(""),
    [selected, D] = useState(null),
    [local, L] = useState(0),
    [error, E] = useState("");
  const result = useData(
    "/alerts?limit=100" +
      (status ? "&status=" + status : "") +
      (severity ? "&severity=" + severity : ""),
    refresh + local,
  );
  async function update(status) {
    try {
      const r = await api.patch("/alerts/" + selected.alertId, { status });
      D(r.data);
      L((x) => x + 1);
      E("");
    } catch (e) {
      E(message(e));
    }
  }
  return (
    <main>
      <Title
        eyebrow="DETECTION & RESPONSE"
        title="Alerts"
        description="Investigate suspicious activity and track each finding."
      />
      <div className="filters">
        <label>
          Status
          <select value={status} onChange={(e) => S(e.target.value)}>
            <option value="">All statuses</option>
            {["open", "acknowledged", "resolved"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label>
          Severity
          <select value={severity} onChange={(e) => V(e.target.value)}>
            <option value="">All severities</option>
            <option>WARNING</option>
            <option>CRITICAL</option>
          </select>
        </label>
      </div>
      <ErrorBox error={result.error || error} />
      <section className="panel">
        {result.data?.length ? (
          <AlertTable items={result.data} onSelect={D} />
        ) : (
          <Empty />
        )}
      </section>
      {selected && (
        <div className="modal-backdrop">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="Alert details"
          >
            <button
              className="close"
              onClick={() => D(null)}
              aria-label="Close"
            >
              ×
            </button>
            <Badge value={selected.severity} />
            <h2>Detection details</h2>
            <p>
              {time(selected.ts)} · Score {selected.score}/100
            </p>
            <p>
              ML probability:{" "}
              {selected.mlProbability === null
                ? "Model unavailable"
                : (selected.mlProbability * 100).toFixed(1) + "%"}
            </p>
            <p>{selected.reasons.join(", ")}</p>
            <h3>Affected files</h3>
            <ul className="paths">
              {selected.affectedFiles.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
            <p className="notice">
              Process attribution is best-effort. If a program was suspended,
              verify its identity and resume it manually using your operating
              system’s process management tools. Argus does not resume
              processes.
            </p>
            <div className="actions">
              {["open", "acknowledged", "resolved"].map((s) => (
                <button
                  className="secondary"
                  key={s}
                  disabled={s === selected.status}
                  onClick={() => update(s)}
                >
                  {s}
                </button>
              ))}
            </div>
            <ErrorBox error={error} />
          </section>
        </div>
      )}
    </main>
  );
}
