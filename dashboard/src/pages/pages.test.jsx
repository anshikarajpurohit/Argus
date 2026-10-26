import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
vi.mock("../api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
  getToken: () => null,
  setToken: vi.fn(),
  message: (e) => e.message,
}));
vi.mock("../hooks/useData", () => ({
  useData: (path) => ({
    data:
      path === "/settings"
        ? {
            responseMode: "alert_only",
            warningThreshold: 40,
            criticalThreshold: 70,
            processAllowlist: ["node"],
          }
        : path === "/stats/summary"
          ? {
              eventsLast24h: 0,
              alertsOpen: 0,
              alertsCritical24h: 0,
              filesAffected24h: 0,
            }
          : [],
    error: "",
    setData: vi.fn(),
  }),
}));
import Login from "./Login";
import Overview from "./Overview";
import Alerts from "./Alerts";
import Events from "./Events";
import Settings from "./Settings";
import Vault from "./Vault";
const render = (Component) =>
  renderToStaticMarkup(
    <MemoryRouter>
      <Component refresh={0} />
    </MemoryRouter>,
  );
describe("page rendering", () => {
  it("login has accessible credentials fields", () => {
    const html = render(Login);
    expect(html).toContain('autoComplete="username"');
    expect(html).toContain('type="password"');
  });
  it("overview presents real zero counts without invented activity", () => {
    const html = render(Overview);
    expect(html).toContain("No alerts to review");
    expect(html).toContain("Normal");
  });
  it("alerts exposes severity and status filters", () => {
    const html = render(Alerts);
    expect(html).toContain("All severities");
    expect(html).toContain("All statuses");
  });
  it("events exposes action, canary, and time filters", () => {
    const html = render(Events);
    expect(html).toContain("Canaries only");
    expect(html).toContain("datetime-local");
  });
  it("settings preserves alert-only and explains suspension", () => {
    const html = render(Settings);
    expect(html).toContain(
      "Suspend mode may freeze a legitimate program if misidentified",
    );
    expect(html).not.toContain('checked=""');
  });
  it("vault communicates limit and empty state", () => {
    const html = render(Vault);
    expect(html).toContain("50 MB");
    expect(html).toContain("Your vault is empty");
    expect(html).toContain('type="password"');
  });
});
