export function securityStatus(alerts, now = Date.now() / 1000) {
  const newest = alerts
    .filter((a) => a.status === "open" && a.ts >= now - 300)
    .sort((a, b) => b.ts - a.ts)[0];
  return newest?.severity === "CRITICAL"
    ? "Critical"
    : newest
      ? "Warning"
      : "Normal";
}
export function mergeAlert(items, item) {
  return [item, ...items.filter((a) => a.alertId !== item.alertId)]
    .sort((a, b) => b.ts - a.ts)
    .slice(0, 100);
}
export function byteSize(size) {
  return size >= 1048576
    ? `${(size / 1048576).toFixed(1)} MB`
    : size >= 1024
      ? `${(size / 1024).toFixed(1)} KB`
      : `${size} B`;
}
