import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { api, getToken, setToken, message } from '../api';
import { Badge, ErrorBox, Empty, Title, AlertTable, time } from '../components/common';
import { useData } from '../hooks/useData';
import { securityStatus, byteSize } from '../helpers';
export default function Login() {
  const [username, U] = useState(""),
    [password, P] = useState(""),
    [error, E] = useState(""),
    [busy, B] = useState(false);
  const navigate = useNavigate();
  async function submit(e) {
    e.preventDefault();
    B(true);
    E("");
    try {
      const r = await api.post("/auth/login", { username, password });
      setToken(r.data.token);
      navigate("/");
    } catch (e) {
      E(message(e));
    } finally {
      B(false);
      P("");
    }
  }
  return (
    <main className="login">
      <section className="login-brand">
        <div className="logo">◈ ARGUS</div>
        <h1>
          A clearer view.
          <br />A stronger defense.
        </h1>
        <p>
          Endpoint monitoring, behavioral detection, and secure file protection
          in one workspace.
        </p>
        <div className="radar">
          <i />
          <i />
          <i />
          <span>◈</span>
        </div>
        <small>LOCAL MONITORING · EDUCATIONAL PROTOTYPE</small>
      </section>
      <section className="login-form">
        <p className="eyebrow">SECURITY WORKSPACE</p>
        <h2>Welcome back</h2>
        <p>Sign in to your Argus dashboard.</p>
        <form onSubmit={submit}>
          <label>
            Username
            <input
              autoComplete="username"
              value={username}
              onChange={(e) => U(e.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => P(e.target.value)}
              required
            />
          </label>
          <ErrorBox error={error} />
          <button disabled={busy} type="submit">
            {busy ? "Signing in…" : "Sign in →"}
          </button>
        </form>
        <small>Use the administrator credentials created during setup.</small>
      </section>
    </main>
  );
}
