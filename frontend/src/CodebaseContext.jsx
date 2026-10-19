import { createContext, useContext, useState } from "react";
import { api } from "./api";

const CodebaseContext = createContext(null);
export const useCodebase = () => useContext(CodebaseContext);

export function CodebaseProvider({ children }) {
  const [path, setPath] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | ready | error
  const [message, setMessage] = useState("");

  async function ingest() {
    const p = path.trim();
    if (!p) {
      setStatus("error");
      setMessage("Enter a repo URL first");
      return;
    }
    setStatus("loading");
    setMessage("Scanning and embedding files...");
    try {
      const data = await api("/ingest", { codebase_path: p });
      setStatus("ready");
      setMessage(`${data.files_found} files · ${data.chunks_stored} chunks`);
    } catch (e) {
      setStatus("error");
      setMessage(e.message);
    }
  }

  return (
    <CodebaseContext.Provider
      value={{ path: path.trim(), setPath, status, message, ingest, isReady: status === "ready" }}
    >
      {children}
    </CodebaseContext.Provider>
  );
}