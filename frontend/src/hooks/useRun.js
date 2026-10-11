import { useState } from "react";

// Runs any async call and tracks loading / error / result / time taken
export function useRun() {
  const [state, setState] = useState({ status: "idle", data: null, error: "", seconds: 0 });

  async function run(fn) {
    const t0 = Date.now();
    const secs = () => ((Date.now() - t0) / 1000).toFixed(1);
    setState({ status: "loading", data: null, error: "", seconds: 0 });
    try {
      const data = await fn();
      setState({ status: "done", data, error: "", seconds: secs() });
    } catch (e) {
      setState({ status: "error", data: null, error: e.message, seconds: secs() });
    }
  }

  return { ...state, run, busy: state.status === "loading" };
}