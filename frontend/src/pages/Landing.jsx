import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import Logo from "../components/Logo";
import Ghost from "../components/Ghost";
import { TOOLS } from "../tools";
import { useAuth } from "../AuthContext";

const STEPS = [
  { n: "01", title: "Add a repo", text: "Paste any public GitHub URL. Wraith reads and indexes every file." },
  { n: "02", title: "Pick a tool", text: "Ask questions, run an agent, scan for bugs, solve issues or research." },
  { n: "03", title: "Get answers", text: "Every answer comes with the source files it was found in." },
];

export default function Landing() {
  const { isLoggedIn, username, openAuth } = useAuth();

  return (
    <div className="landing">
      <header className="land-nav">
        <Logo />
        <div className="land-nav-right">
          {isLoggedIn ? (
            <>
              <span className="muted">{username}</span>
              <Link to="/app" className="btn btn-primary">Open app</Link>
            </>
          ) : (
            <>
              <button className="btn btn-ghost" onClick={() => openAuth("login")}>Log in</button>
              <button className="btn btn-primary" onClick={() => openAuth("signup")}>Sign up</button>
            </>
          )}
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <span className="pill">Codebase intelligence</span>
          <h1>
            Understand any codebase.<br />
            <span className="grad">Haunt it with questions.</span>
          </h1>
          <p className="muted hero-sub">
            Wraith reads a GitHub repo and answers questions about it, finds bugs,
            solves issues and researches fixes, all grounded in your actual code.
          </p>
          <div className="hero-cta">
            <Link to="/app" className="btn btn-primary btn-lg">
              Launch Wraith <ArrowRight size={16} />
            </Link>
            {!isLoggedIn && (
              <button className="btn btn-ghost btn-lg" onClick={() => openAuth("signup")}>
                Create account
              </button>
            )}
          </div>
          <p className="muted hero-note">No account needed to try it.</p>
        </div>
        <div className="hero-art">
          <Ghost size={240} />
        </div>
      </section>

      <section className="land-section">
        <h2>Five tools, one codebase</h2>
        <div className="feature-grid">
          {TOOLS.map(({ id, label, icon: Icon, desc }) => (
            <Link to={`/app/${id}`} className="feature-card" key={id}>
              <div className="feature-icon"><Icon size={20} /></div>
              <h3>{label}</h3>
              <p className="muted">{desc}</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="land-section">
        <h2>How it works</h2>
        <div className="step-grid">
          {STEPS.map((s) => (
            <div className="step-card" key={s.n}>
              <span className="step-n">{s.n}</span>
              <h3>{s.title}</h3>
              <p className="muted">{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="land-footer">
        <Logo size={20} />
        <span className="muted">Built by Omika</span>
      </footer>
    </div>
  );
}