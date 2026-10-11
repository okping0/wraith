import { useState } from "react";
import { useAuth } from "../AuthContext";
import { API_URL } from "../api";
import Logo from "./Logo";

export default function AuthModal() {
  const { modal, closeAuth, openAuth, login, register } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (!modal) return null;
  const isSignup = modal === "signup";

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (isSignup && !username.trim()) return setError("Username is required");
    setBusy(true);
    try {
      if (isSignup) await register(username.trim(), email, password);
      else await login(email, password);
      setPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function switchMode() {
    setError("");
    openAuth(isSignup ? "login" : "signup");
  }

  return (
    <div className="modal-backdrop" onClick={closeAuth}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <Logo />
        <h2>{isSignup ? "Create your account" : "Welcome back"}</h2>
        <p className="muted">
          {isSignup ? "Save your work and unlock more." : "Log in to continue."}
        </p>

        {isSignup && (
          <input
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        )}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className="modal-error">{error}</p>}

        <button className="btn btn-primary" disabled={busy}>
          {busy ? "Please wait..." : isSignup ? "Sign up" : "Log in"}
        </button>

        <div className="modal-divider"><span>or</span></div>

        <a className="btn btn-ghost" href={`${API_URL}/auth/github/login`}>
          Continue with GitHub
        </a>

        <p className="muted modal-switch">
          {isSignup ? "Already have an account?" : "New here?"}{" "}
          <button type="button" onClick={switchMode}>
            {isSignup ? "Log in" : "Sign up"}
          </button>
        </p>
      </form>
    </div>
  );
}