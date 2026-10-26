import React,{useState,useEffect} from 'react';
import {NavLink,Routes,Route,Navigate,useNavigate} from 'react-router-dom';
import {io} from 'socket.io-client';
import {getToken,setToken} from '../api';
import Overview from '../pages/Overview';
import Alerts from '../pages/Alerts';
import Events from '../pages/Events';
import Settings from '../pages/Settings';
import Vault from '../pages/Vault';
export default function Shell() {
  const [connected, C] = useState(false),
    [refresh, R] = useState(0);
  const navigate = useNavigate();
  useEffect(() => {
    const socket = io(
      import.meta.env.VITE_SOCKET_URL || window.location.origin,
      { auth: { token: getToken() } },
    );
    socket.on("connect", () => { C(true); R(x => x + 1); });
    socket.on("disconnect", () => C(false));
    socket.on("connect_error", () => C(false));
    for (const name of ["alert:new", "event:new", "settings:updated"])
      socket.on(name, () => R((x) => x + 1));
    return () => socket.disconnect();
  }, []);
  return (
    <div className="shell">
      <aside>
        <NavLink to="/" className="logo">
          ◈ ARGUS
        </NavLink>
        <p className="nav-label">WORKSPACE</p>
        <nav>
          {[
            ["/", "◫", "Overview"],
            ["/alerts", "◇", "Alerts"],
            ["/events", "≋", "Events"],
            ["/vault", "▣", "Secure vault"],
            ["/settings", "⚙", "Settings"],
          ].map(([to, icon, label]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              <span>{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className={"connection " + (connected ? "online" : "")}>
            <b />
            Dashboard {connected ? "connected" : "disconnected"}
          </div>
          <small>
            Educational EDR prototype
            <br />
            Agent health is not inferred from this connection.
          </small>
          <button
            className="ghost"
            onClick={() => {
              setToken(null);
              navigate("/login");
            }}
          >
            Sign out ↗
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header>
          <span>
            Security operations <span className="slash">/</span> Local endpoint
          </span>
          <span className="avatar">A</span>
        </header>
        <Routes>
          <Route path="/" element={<Overview refresh={refresh} />} />
          <Route path="/alerts" element={<Alerts refresh={refresh} />} />
          <Route path="/events" element={<Events refresh={refresh} />} />
          <Route path="/vault" element={<Vault />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </div>
  );
}
