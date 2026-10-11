import { useState } from "react";
import { api } from "../../api";
import { useCodebase } from "../../CodebaseContext";
import { useRun } from "../../hooks/useRun";
import PromptBox from "../../components/PromptBox";
import Answer from "../../components/Answer";
import Markdown from "../../components/Markdown";

export default function Agent() {
  const { path } = useCodebase();
  const [question, setQuestion] = useState("");
  const { status, data, error, seconds, run, busy } = useRun();

  function submit() {
    if (!question.trim() || busy) return;
    run(() => api("/agent", { codebase_path: path, question: question.trim() }));
  }

  return (
    <>
      <PromptBox
        value={question}
        onChange={setQuestion}
        onSubmit={submit}
        busy={busy}
        button="Run agent"
        placeholder="Find bugs in the login flow and explain how to fix them"
      />
      <Answer status={status} error={error} seconds={seconds} loadingText="Agent reasoning... this can take a minute">
        <Markdown text={data?.answer} />
      </Answer>
    </>
  );
}