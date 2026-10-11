import { useState } from "react";
import { Send, FileCode } from "lucide-react";
import { api } from "../../api";
import { useCodebase } from "../../CodebaseContext";
import { useRun } from "../../hooks/useRun";
import Answer from "../../components/Answer";
import Markdown from "../../components/Markdown";

export default function Ask() {
  const { path } = useCodebase();
  const [question, setQuestion] = useState("");
  const { status, data, error, seconds, run, busy } = useRun();

  function submit() {
    if (!question.trim() || busy) return;
    run(() => api("/ask", { codebase_path: path, question: question.trim() }));
  }

  return (
    <>
      <div className="input-box">
        <textarea
          rows={3}
          placeholder="How is authentication implemented?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => (e.ctrlKey || e.metaKey) && e.key === "Enter" && submit()}
        />
        <div className="input-foot">
          <span className="muted">Ctrl + Enter to send</span>
          <button className="btn btn-primary" onClick={submit} disabled={busy || !question.trim()}>
            <Send size={14} /> Ask
          </button>
        </div>
      </div>

      <Answer status={status} error={error} seconds={seconds} loadingText="Searching the codebase...">
        <Markdown text={data?.answer} />

        {data?.sources?.length > 0 && (
          <div className="sources">
            <h4 className="side-label">Sources ({data.sources.length})</h4>
            {data.sources.map((s, i) => (
              <div className="source-row" key={i}>
                <FileCode size={14} />
                <span className="mono">{s.file}</span>
                {s.lines && <span className="muted mono">lines {s.lines}</span>}
              </div>
            ))}
          </div>
        )}
      </Answer>
    </>
  );
}