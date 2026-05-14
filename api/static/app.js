const API = "http://localhost:8000";

// ─── PANEL NAVIGATION ───────────────────────────────────────────
function showPanel(name, clickedEl) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById("panel-" + name).classList.add("active");
  clickedEl.classList.add("active");
}

// ─── HELPERS ────────────────────────────────────────────────────
function getPath() {
  return document.getElementById("globalPath").value.trim();
}

function setLoading(outputId, message = "Processing...") {
  const el = document.getElementById(outputId);
  el.className = "output loading";
  el.innerHTML = `<div class="spinner"></div><span>${message}</span>`;
}

function setOutput(outputId, text) {
  const el = document.getElementById(outputId);
  el.className = "output rendered";
  el.innerHTML = marked.parse(String(text));
}

function setError(outputId, message) {
  const el = document.getElementById(outputId);
  el.className = "output error";
  el.textContent = "✗ " + message;
}

function setPlaceholder(outputId, message = "Waiting for input...") {
  const el = document.getElementById(outputId);
  el.className = "output placeholder";
  el.textContent = message;
}

function setBtn(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? "Running..." : btn.dataset.label;
}

// ─── INGEST ─────────────────────────────────────────────────────
async function ingest() {
  const path = getPath();
  if (!path) {
    document.getElementById("ingestStatus").innerHTML =
      `<span class="tag-error">✗ Enter a codebase path first</span>`;
    return;
  }

  const btn = document.querySelector(".btn-ingest");
  btn.disabled = true;
  btn.textContent = "Ingesting...";
  document.getElementById("ingestStatus").innerHTML =
    `<span class="tag-info">Scanning files...</span>`;

  try {
    const res = await fetch(`${API}/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codebase_path: path })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();
    document.getElementById("ingestStatus").innerHTML =
      `<span class="tag-success">✓ ${data.files_found} files · ${data.chunks_stored} chunks</span>`;
  } catch (e) {
    document.getElementById("ingestStatus").innerHTML =
      `<span class="tag-error">✗ ${e.message}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "⚡ INGEST";
  }
}

// ─── ASK ────────────────────────────────────────────────────────
async function runAsk() {
  const path = getPath();
  const question = document.getElementById("askQuestion").value.trim();

  if (!path || !question) {
    setError("askOutput", "Fill in the codebase path and your question.");
    return;
  }

  setLoading("askOutput", "Searching codebase...");
  setBtn("btnAsk", true);
  document.getElementById("askSources").innerHTML = "";

  try {
    const res = await fetch(`${API}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codebase_path: path, question })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();
    setOutput("askOutput", data.answer);

    if (data.sources && data.sources.length > 0) {
      document.getElementById("askSources").innerHTML = data.sources
        .map(s => `<div class="source-tag">${s.file}${s.lines ? " · " + s.lines : ""}</div>`)
        .join("");
    }
  } catch (e) {
    setError("askOutput", e.message);
  } finally {
    setBtn("btnAsk", false);
  }
}

// ─── AGENT ──────────────────────────────────────────────────────
async function runAgent() {
  const path = getPath();
  const question = document.getElementById("agentQuestion").value.trim();

  if (!path || !question) {
    setError("agentOutput", "Fill in the codebase path and your question.");
    return;
  }

  setLoading("agentOutput", "Agent reasoning... this may take a moment");
  setBtn("btnAgent", true);

  try {
    const res = await fetch(`${API}/agent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codebase_path: path, question })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();
    setOutput("agentOutput", data.answer);
  } catch (e) {
    setError("agentOutput", e.message);
  } finally {
    setBtn("btnAgent", false);
  }
}

// ─── ANALYZE ────────────────────────────────────────────────────
async function runAnalyze() {
  const path = getPath();

  if (!path) {
    setError("analyzeOutput", "Enter a codebase path first.");
    return;
  }

  setLoading("analyzeOutput", "Analyzing codebase... this may take a minute");
  setBtn("btnAnalyze", true);

  try {
    const res = await fetch(`${API}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codebase_path: path })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();

    // Format file analysis results as markdown
    let md = "";

    if (data.file_analysis && data.file_analysis.length > 0) {
      md += "## File Analysis\n\n";
      for (const r of data.file_analysis) {
        md += `### \`${r.file}\`\n\n${r.issues}\n\n---\n\n`;
      }
    }

    if (data.security_scan) {
      md += "## Security Scan\n\n" + JSON.stringify(data.security_scan, null, 2);
    }

    setOutput("analyzeOutput", md || "No issues found.");
  } catch (e) {
    setError("analyzeOutput", e.message);
  } finally {
    setBtn("btnAnalyze", false);
  }
}

// ─── ISSUE ──────────────────────────────────────────────────────
async function runIssue() {
  const path = getPath();
  const url = document.getElementById("issueUrl").value.trim();

  if (!path || !url) {
    setError("issueOutput", "Fill in the codebase path and GitHub issue URL.");
    return;
  }

  setLoading("issueOutput", "Fetching and analyzing issue...");
  setBtn("btnIssue", true);

  try {
    const res = await fetch(`${API}/issue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codebase_path: path, issue_url: url })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();
    setOutput("issueOutput", data.analysis || data.error || "No analysis returned.");
  } catch (e) {
    setError("issueOutput", e.message);
  } finally {
    setBtn("btnIssue", false);
  }
}

// ─── RESEARCH ───────────────────────────────────────────────────
async function runResearch() {
  const path = getPath();
  const problem = document.getElementById("researchProblem").value.trim();

  if (!path || !problem) {
    setError("researchOutput", "Fill in the codebase path and your problem.");
    return;
  }

  setLoading("researchOutput", "Searching the web...");
  setBtn("btnResearch", true);

  try {
    const res = await fetch(`${API}/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codebase_path: path, problem })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();

    const stackStr = data.stack
      ? `**Detected stack:** ${Array.isArray(data.stack) ? data.stack.join(", ") : JSON.stringify(data.stack)}\n\n---\n\n`
      : "";

    setOutput("researchOutput", stackStr + (data.recommendation || "No recommendation returned."));
  } catch (e) {
    setError("researchOutput", e.message);
  } finally {
    setBtn("btnResearch", false);
  }
}