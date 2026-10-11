import { ScanSearch } from "lucide-react";
import { api } from "../../api";
import { useCodebase } from "../../CodebaseContext";
import { useRun } from "../../hooks/useRun";
import Answer from "../../components/Answer";
import Markdown from "../../components/Markdown";

function toMarkdown(data) {
  let md = "";
  if (data.file_analysis?.length) {
    md += "## File analysis\n\n";
    for (const r of data.file_analysis) {
      md += `### \`${r.file}\`\n\n${r.issues}\n\n---\n\n`;
    }
  }
  if (data.security_scan) {
    md += "## Security scan\n\n```json\n" + JSON.stringify(data.security_scan, null, 2) + "\n```";
  }
  return md || "No issues found.";
}

export default function Analyze() {
  const { path } = useCodebase();
  const { status, data, error, seconds, run, busy } = useRun();

  return (
    <>
      <div className="input-box">
        <div className="input-foot" style={{ marginTop: 0 }}>
          <span className="muted">Scans every ingested file for bugs and vulnerabilities.</span>
          <button
            className="btn btn-primary"
            disabled={busy}
            onClick={() => run(() => api("/analyze", { codebase_path: path }))}
          >
            <ScanSearch size={14} /> Run analysis
          </button>
        </div>
      </div>
      <Answer status={status} error={error} seconds={seconds} loadingText="Analyzing codebase... this may take a minute">
        <Markdown text={data && toMarkdown(data)} />
      </Answer>
    </>
  );
}