import { Send } from "lucide-react";

export default function PromptBox({ value, onChange, onSubmit, busy, placeholder, button = "Run", rows = 3 }) {
  return (
    <div className="input-box">
      <textarea
        rows={rows}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          const send = rows === 1 ? e.key === "Enter" : (e.ctrlKey || e.metaKey) && e.key === "Enter";
          if (send) { e.preventDefault(); onSubmit(); }
        }}
      />
      <div className="input-foot">
        <span className="muted">{rows === 1 ? "Enter to send" : "Ctrl + Enter to send"}</span>
        <button className="btn btn-primary" onClick={onSubmit} disabled={busy || !value.trim()}>
          <Send size={14} /> {button}
        </button>
      </div>
    </div>
  );
}