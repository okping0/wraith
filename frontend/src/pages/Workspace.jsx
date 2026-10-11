import { Routes, Route, Navigate, useParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Ghost from "../components/Ghost";
import { TOOLS } from "../tools";
import { useAuth } from "../AuthContext";
import { useCodebase } from "../CodebaseContext";

import Ask from "./tools/Ask";
import Agent from "./tools/Agent";
import Analyze from "./tools/Analyze";
import Issues from "./tools/Issues";
import Research from "./tools/Research";

const VIEWS = { ask: Ask, agent: Agent, analyze: Analyze, issues: Issues, research: Research };

function ToolPage() {
  const { tool } = useParams();
  const { isReady } = useCodebase();
  const t = TOOLS.find((x) => x.id === tool);
  if (!t) return <Navigate to="/app/ask" replace />;

  const ActiveView = VIEWS[tool];

  return (
    <div className="tool-page">
      <header className="tool-head">
        <h1>{t.label}</h1>
        <p className="muted">{t.desc}</p>
      </header>

      {!isReady ? (
        <div className="empty-state">
          <Ghost />
          <h3>Nothing to haunt yet</h3>
          <p className="muted">Paste a GitHub repo URL in the sidebar and click Ingest to unlock this tool.</p>
        </div>
      ) : VIEWS[tool] ? (
        <ActiveView />
      ) : (
        <div className="empty-state">
          <p className="muted">{t.label} UI goes here (next step).</p>
        </div>
      )}
    </div>
  );
}

export default function Workspace() {
  const { isLoggedIn, openAuth } = useAuth();
  return (
    <div className="shell">
      <Sidebar />
      <main className="main">
        {!isLoggedIn && (
          <div className="guest-banner">
            You're using Wraith as a guest.
            <button onClick={() => openAuth("signup")}>Sign up</button> to save your work.
          </div>
        )}
        <Routes>
          <Route index element={<Navigate to="ask" replace />} />
          <Route path=":tool" element={<ToolPage />} />
        </Routes>
      </main>
    </div>
  );
}