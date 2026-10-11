import { useState } from "react";
import { api } from "../../api";
import { useCodebase } from "../../CodebaseContext";
import { useRun } from "../../hooks/useRun";
import PromptBox from "../../components/PromptBox";
import Answer from "../../components/Answer";
import Markdown from "../../components/Markdown";

export default function Issues() {
  const { path } = useCodebase();
  const [url, setUrl] = useState("");
  const { status, data, error, seconds, run, busy } = useRun();

  function submit() {
    if (!url.trim() || busy) return;
    run(() => api("/issue", { codebase_path: path, issue_url: url.trim() }));
  }

  return (
    <>
      <PromptBox
        rows={1}
        value={url}
        onChange={setUrl}
        onSubmit={submit}
        busy={busy}
        button="Solve"
        placeholder="https://github.com/owner/repo/issues/1"
      />
      <Answer status={status} error={error} seconds={seconds} loadingText="Fetching and analyzing the issue...">
        <Markdown text={data?.analysis || data?.error || "No analysis returned."} />
      </Answer>
    </>
  );
}