import { useEffect, useState } from "react";
import { Eye, EyeOff, Check, Circle } from "lucide-react";
import { useAuth } from "../AuthContext";
import { API_URL } from "../api";
import Logo from "./Logo";

const RULES = [
  { label: "8+ characters", test: (p) => p.length >= 8 },
  { label: "Uppercase letter", test: (p) => /[A-Z]/.test(p) },
  { label: "Lowercase letter", test: (p) => /[a-z]/.test(p) },
  { label: "A number", test: (p) => /\d/.test(p) },
  { label: "Special character", test: (p) => /[^A-Za-z0-9]/.test(p) },
];

export default function AuthModal() {
  const { modal, closeAuth, openAuth, login, register } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setError("");
    setPassword("");
    setConfirm("");
    setShow(false);
  }, [modal]);

  if (!modal) return null;
  const isSignup = modal === "signup";
  const allRulesPass = RULES.every((r) => r.test(password));
  const mismatch = confirm && password !== confirm;

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (isSignup) {
      if (!username.trim()) return setError("Username is required");
      if (!allRulesPass) return setError("Password doesn't meet all requirements");
      if (password !== confirm) return setError("Passwords don't match");
    }
    setBusy(true);
    try {
      if (isSignup) await register(username.trim(), email.trim(), password);
      else await login(email.trim(), password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
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
          <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        )}
        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />

        <div className="pw-wrap">
          <input
            type={show ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="button" className="pw-toggle" onClick={() => setShow(!show)} tabIndex={-1}>
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>

        {isSignup && (
          <>
            <ul className="pw-rules">
              {RULES.map((r) => {
                const ok = r.test(password);
                return (
                  <li key={r.label} className={ok ? "ok" : ""}>
                    {ok ? <Check size={13} /> : <Circle size={13} />} {r.label}
                  </li>
                );
              })}
            </ul>
            <input
              type={show ? "text" : "password"}
              placeholder="Confirm password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
            {mismatch && <p className="modal-error">Passwords don't match</p>}
          </>
        )}

        {error && <p className="modal-error">{error}</p>}

        <button className="btn btn-primary" disabled={busy || (isSignup && (!allRulesPass || password !== confirm))}>
          {busy ? "Please wait..." : isSignup ? "Sign up" : "Log in"}
        </button>

        <div className="modal-divider"><span>or</span></div>

        <a className="btn btn-ghost" href={`${API_URL}/auth/github/login`}>
          Continue with GitHub
        </a>

        <p className="muted modal-switch">
          {isSignup ? "Already have an account?" : "New here?"}{" "}
          <button type="button" onClick={() => openAuth(isSignup ? "login" : "signup")}>
            {isSignup ? "Log in" : "Sign up"}
          </button>
        </p>
      </form>
    </div>
  );
}