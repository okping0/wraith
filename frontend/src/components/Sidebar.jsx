import { NavLink, Link } from "react-router-dom";
import { Loader2, Sparkles, LogOut, LogIn } from "lucide-react";
import Logo from "./Logo";
import { TOOLS } from "../tools";
import { useAuth } from "../AuthContext";
import { useCodebase } from "../CodebaseContext";

export default function Sidebar() {
  const { isLoggedIn, username, openAuth, logout } = useAuth();
  const { path, setPath, status, message, ingest, isReady } = useCodebase();

  return (
    <aside className="sidebar">
      <Link to="/" className="sidebar-logo"><Logo /></Link>

      <section className="side-section">
        <h4 className="side-label">1 · Codebase</h4>
        <input
          className="mono"
          placeholder="https://github.com/owner/repo"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ingest()}
        />
        <button className="btn btn-primary" onClick={ingest} disabled={status === "loading"}>
          {status === "loading" ? (
            <><Loader2 size={14} className="spin" /> Ingesting...</>
          ) : (
            <><Sparkles size={14} /> Ingest</>
          )}
        </button>
        {message && <p className={`ingest-msg ${status}`}>{message}</p>}
      </section>

      <section className="side-section">
        <h4 className="side-label">2 · Tools</h4>
        <nav className="tool-list">
          {TOOLS.map(({ id, label, icon: Icon }) => (
            <NavLink
              key={id}
              to={`/app/${id}`}
              className={({ isActive }) => `tool-link ${isActive ? "active" : ""} ${isReady ? "" : "locked"}`}
            >
              <Icon size={16} /> {label}
            </NavLink>
          ))}
        </nav>
      </section>

      <div className="side-account">
        {isLoggedIn ? (
          <>
            <div className="avatar">{(username || "?")[0].toUpperCase()}</div>
            <div className="account-name">{username || "..."}</div>
            <button className="icon-btn" onClick={logout} title="Log out"><LogOut size={16} /></button>
          </>
        ) : (
          <button className="btn btn-ghost" style={{ width: "100%" }} onClick={() => openAuth("login")}>
            <LogIn size={14} /> Log in / Sign up
          </button>
        )}
      </div>
    </aside>
  );
}