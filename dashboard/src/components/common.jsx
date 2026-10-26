import React from 'react';
export const time = (ts) => new Date(ts * 1000).toLocaleString();
export const Badge = ({ value }) => (
  <span className={"badge " + value.toLowerCase()}>{value}</span>
);
export function ErrorBox({ error }) {
  return error ? (
    <div className="error" role="alert">
      {error}
    </div>
  ) : null;
}
export function Empty({ text = "No records yet", description = "Activity from your connected agent will appear here." }) {
  return (
    <div className="empty">
      <span>◎</span>
      <strong>{text}</strong>
      <p>{description}</p>
    </div>
  );
}
export function Title({ eyebrow, title, description, children }) {
  return (
    <div className="title">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children}
    </div>
  );
}
export function AlertTable({ items, onSelect }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {[
              "Severity",
              "Detected",
              "Score / reasons",
              "Suspect process",
              "Response",
              "Status",
            ].map((x) => (
              <th key={x}>{x}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr key={a.alertId}>
              <td>
                <button
                  className="cell-button"
                  disabled={!onSelect}
                  onClick={() => onSelect?.(a)}
                >
                  <Badge value={a.severity} />
                </button>
              </td>
              <td>{time(a.ts)}</td>
              <td>
                <strong>{a.score}</strong>
                <small>{a.reasons.join(", ").replaceAll("_", " ")}</small>
              </td>
              <td>
                {a.suspectProcess || "Unknown"}
                {a.suspectPid && (
                  <small>PID {a.suspectPid} · best-effort</small>
                )}
              </td>
              <td>{a.responseTaken.replaceAll("_", " ")}</td>
              <td>
                <Badge value={a.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
