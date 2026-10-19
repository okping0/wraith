import { Loader2, AlertCircle, Clock } from "lucide-react";

export default function Answer({ status, error, seconds, loadingText = "Thinking...", children }) {
  if (status === "idle") return null;

  return (
    <section className="answer">
      <div className="answer-head">
        <span>Wraith</span>
        {status === "loading" && <span className="chip"><Loader2 size={12} className="spin" /> Running</span>}
        {status === "done" && <span className="chip ok"><Clock size={12} /> {seconds}s</span>}
        {status === "error" && <span className="chip err">Failed</span>}
      </div>

      {status === "loading" && <p className="muted">{loadingText}</p>}
      {status === "error" && (
        <p className="answer-error"><AlertCircle size={14} /> {error}</p>
      )}
      {status === "done" && children}
    </section>
  );
}