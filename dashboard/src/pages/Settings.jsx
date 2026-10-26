import React, { useState } from "react";
import { api, message } from "../api";
import { ErrorBox, Title } from "../components/common";
import { useData } from "../hooks/useData";
export default function Settings() {
  const { data, setData, error } = useData("/settings");
  const [notice, N] = useState(""),
    [err, E] = useState(""),
    [busy, B] = useState(false);
  async function save(e) {
    e.preventDefault();
    B(true);
    E("");
    N("");
    try {
      const saved = {
        ...data,
        processAllowlist: data.processAllowlist
          .map((name) => name.trim())
          .filter(Boolean),
      };
      await api.put("/settings", saved);
      setData(saved);
      N("Settings saved. The agent refreshes its settings within 30 seconds.");
    } catch (e) {
      E(message(e));
    } finally {
      B(false);
    }
  }
  return (
    <main>
      <Title
        eyebrow="AGENT CONFIGURATION"
        title="Settings"
        description="Choose how Argus detects and responds to activity."
      />
      <ErrorBox error={error || err} />
      {data && (
        <form onSubmit={save} className="panel settings">
          <section>
            <h2>Response mode</h2>
            <p>
              Choose the action taken when a critical alert has a suspect
              process.
            </p>
            <label className="inline">
              <input
                type="checkbox"
                checked={data.responseMode === "suspend"}
                onChange={(e) =>
                  setData({
                    ...data,
                    responseMode: e.target.checked ? "suspend" : "alert_only",
                  })
                }
              />
              Suspend suspect processes
            </label>
            <p className="notice">
              Suspend mode may freeze a legitimate program if misidentified
            </p>
          </section>
          <section>
            <h2>Detection thresholds</h2>
            <p>
              The warning threshold must remain below the critical threshold.
            </p>
            {[
              ["warningThreshold", "Warning"],
              ["criticalThreshold", "Critical"],
            ].map(([key, label]) => (
              <label key={key}>
                {label} <strong>{data[key]}</strong>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={data[key]}
                  onChange={(e) =>
                    setData({ ...data, [key]: Number(e.target.value) })
                  }
                />
              </label>
            ))}
          </section>
          <section>
            <h2>Process allowlist</h2>
            <label>
              One process name per line
              <textarea
                rows="7"
                value={data.processAllowlist.join("\n")}
                onChange={(e) =>
                  setData({
                    ...data,
                    processAllowlist: e.target.value.split("\n"),
                  })
                }
              />
            </label>
            <small>
              Allowlisted processes are never suspended. Agent and system PIDs
              also have built-in protection.
            </small>
          </section>
          {notice && (
            <p role="status" className="success">
              {notice}
            </p>
          )}
          <button
            disabled={busy || data.warningThreshold >= data.criticalThreshold}
          >
            {busy ? "Saving…" : "Save settings"}
          </button>
        </form>
      )}
    </main>
  );
}
