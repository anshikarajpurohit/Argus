import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { api, getToken, setToken, message } from '../api';
import { Badge, ErrorBox, Empty, Title, AlertTable, time } from '../components/common';
import { useData } from '../hooks/useData';
import { securityStatus, byteSize } from '../helpers';
export default function Vault() {
  const [refresh, R] = useState(0),
    [file, F] = useState(null),
    [password, P] = useState(""),
    [error, E] = useState(""),
    [busy, B] = useState(false),
    [decryptItem, D] = useState(null),
    [decryptPassword, DP] = useState("");
  const result = useData("/vault", refresh);
  async function upload(e) {
    e.preventDefault();
    if (!file) return;
    if (file.size > 50 * 1024 * 1024) {
      E("File exceeds 50 MB");
      return;
    }
    B(true);
    E("");
    const form = new FormData();
    form.append("file", file);
    form.append("password", password);
    try {
      await api.post("/vault/upload", form);
      P("");
      F(null);
      e.target.reset();
      R((x) => x + 1);
    } catch (e) {
      E(message(e));
    } finally {
      B(false);
    }
  }
  async function download(e) {
    e.preventDefault();
    B(true);
    try {
      const r = await api.post(
        "/vault/" + decryptItem.itemId + "/decrypt",
        { password: decryptPassword },
        { responseType: "blob" },
      );
      const url = URL.createObjectURL(r.data),
        a = document.createElement("a");
      a.href = url;
      a.download = decryptItem.originalName;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      D(null);
      E("");
    } catch (e) {
      E(e.response?.status === 403 ? "Decryption failed" : message(e));
    } finally {
      DP("");
      B(false);
    }
  }
  async function remove(item) {
    if (
      !confirm("Permanently delete " + item.originalName + " from the vault?")
    )
      return;
    try {
      await api.delete("/vault/" + item.itemId);
      R((x) => x + 1);
    } catch (e) {
      E(message(e));
    }
  }
  return (
    <main>
      <Title
        eyebrow="ENCRYPTED FILE STORAGE"
        title="Secure vault"
        description="Protect files you explicitly submit with password-based encryption."
      >
        <span className="badge normal">AES-256-GCM</span>
      </Title>
      <ErrorBox error={error || result.error} />
      <form onSubmit={upload} className="panel upload">
        <div>
          <h2>Add a protected file</h2>
          <p>Up to 50 MB. Your password is never stored.</p>
        </div>
        <label>
          File
          <input type="file" required onChange={(e) => F(e.target.files[0])} />
        </label>
        <label>
          Encryption password
          <input
            type="password"
            minLength="1"
            required
            value={password}
            autoComplete="new-password"
            onChange={(e) => P(e.target.value)}
          />
        </label>
        <button disabled={busy}>
          {busy ? "Working…" : "Encrypt & upload"}
        </button>
      </form>
      <section className="panel">
        <div className="panel-head">
          <h2>Protected files</h2>
          <span>{result.data?.length ?? 0} files</span>
        </div>
        {result.data?.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Size</th>
                  <th>Added</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {result.data.map((item) => (
                  <tr key={item.itemId}>
                    <td>{item.originalName}</td>
                    <td>{byteSize(item.sizeBytes)}</td>
                    <td>{new Date(item.createdAt).toLocaleString()}</td>
                    <td>
                      <div className="actions">
                        <button
                          className="secondary"
                          onClick={() => {
                            D(item);
                            DP("");
                            E("");
                          }}
                        >
                          Decrypt & download
                        </button>
                        <button className="danger" onClick={() => remove(item)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty text="Your vault is empty" />
        )}
      </section>
      <p className="footnote">
        Keep your password somewhere safe. Lost passwords cannot be recovered.
        The vault folder is excluded from monitoring.
      </p>
      {decryptItem && (
        <div className="modal-backdrop">
          <form
            onSubmit={download}
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="Decrypt file"
          >
            <button type="button" className="close" onClick={() => D(null)}>
              ×
            </button>
            <h2>Decrypt {decryptItem.originalName}</h2>
            <label>
              Password
              <input
                autoFocus
                required
                type="password"
                value={decryptPassword}
                onChange={(e) => DP(e.target.value)}
              />
            </label>
            <ErrorBox error={error} />
            <button disabled={busy}>
              {busy ? "Decrypting…" : "Download plaintext file"}
            </button>
          </form>
        </div>
      )}
    </main>
  );
}
