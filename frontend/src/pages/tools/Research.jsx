import { useState } from "react";
import { api } from "../../api";
import { useCodebase } from "../../CodebaseContext";
import { useRun } from "../../hooks/useRun";
import PromptBox from "../../components/PromptBox";
import Answer from "../../components/Answer";
import Markdown from "../../components/Markdown";

export default function Research() {
  const { path } = useCodebase();
  const [problem, setProblem] = useState("");
  const { status, data, error, seconds, run, busy } = useRun();

  function submit() {
    if (!problem.trim() || busy) return;
    run(() => api("/research", { codebase_path: path, problem: problem.trim() }));
  }

  const stack = data?.stack
    ? Array.isArray(data.stack) ? data.stack.join(", ") : JSON.stringify(data.stack)
    : null;

  return (
    <>
      <PromptBox
        value={problem}
        onChange={setProblem}
        onSubmit={submit}
        busy={busy}
        button="Research"
        placeholder="How do I handle database connection pooling?"
      />
      <Answer status={status} error={error} seconds={seconds} loadingText="Searching the web...">
        {stack && <p className="stack-line"><b>Detected stack:</b> <span className="mono">{stack}</span></p>}
        <Markdown text={data?.recommendation || "No recommendation returned."} />
      </Answer>
    </>
  );
}