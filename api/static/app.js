const API = "";

// ─── PANEL NAVIGATION ───────────────────────────────────────────
function showPanel(name, clickedEl) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-tab").forEach(n => n.classList.remove("active"));
  document.getElementById("panel-" + name).classList.add("active");
  clickedEl.classList.add("active");
}

// ─── HELPERS ────────────────────────────────────────────────────
function getPath() {
  return document.getElementById("globalPath").value.trim();
}

function setLoading(outputId, message = "Processing...") {
  const el = document.getElementById(outputId);
  el.className = "response-body loading";
  el.innerHTML = `<div class="spinner"></div><span>${message}</span>`;
}

function setOutput(outputId, text) {
  const el = document.getElementById(outputId);
  el.className = "response-body";
  el.innerHTML = marked.parse(String(text));
}

function setError(outputId, message) {
  const el = document.getElementById(outputId);
  el.className = "response-body error";
  el.textContent = "✗ " + message;
}

function setPlaceholder(outputId, message = "Waiting for input...") {
  const el = document.getElementById(outputId);
  el.className = "response-body placeholder";
  el.textContent = message;
}

function setBtn(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.innerHTML = loading
    ? `<div class="spinner" style="width:12px;height:12px;border-width:2px;"></div>`
    : "▶";
}

function showTiming(prefix, text) {
  const el = document.getElementById(prefix + "Timing");
  const textEl = document.getElementById(prefix + "TimingText");
  if (el) { el.style.display = "flex"; }
  if (textEl) { textEl.textContent = text; }
}

function hideTiming(prefix) {
  const el = document.getElementById(prefix + "Timing");
  if (el) el.style.display = "none";
}

// ─── INGEST ─────────────────────────────────────────────────────
async function ingest() {
  const path = getPath();
  if (!path) {
    document.getElementById("ingestStatusRight").innerHTML =
      `<span class="tag-error">✗ Enter a codebase path first</span>`;
    return;
  }

  const btn = document.querySelector(".btn-ingest");
  btn.disabled = true;
  btn.innerHTML = `<div class="spinner" style="width:11px;height:11px;border-width:2px;display:inline-block;"></div> Ingesting...`;
  document.getElementById("ingestStatusRight").innerHTML =
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

    // Show "Codebase Ready" in header
    document.getElementById("codebaseStatus").style.display = "flex";

    document.getElementById("ingestStatusRight").innerHTML =
      `<span class="tag-success">✓ ${data.files_found} files · ${data.chunks_stored} chunks</span>`;
  } catch (e) {
    document.getElementById("ingestStatusRight").innerHTML =
      `<span class="tag-error">✗ ${e.message}</span>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="ingest-star">✦</span> INGEST`;
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

  const t0 = Date.now();
  setLoading("askOutput", "Searching codebase...");
  setBtn("btnAsk", true);
  showTiming("ask", "Running...");

  // Reset sources
  document.getElementById("askSources").innerHTML = "";
  document.getElementById("askSources").classList.remove("expanded");
  document.getElementById("askSourcesRight").innerHTML =
    `<div style="font-size:13px;color:var(--text-muted);padding:8px 0;text-align:center;">Loading...</div>`;
  document.getElementById("askViewAll").style.display = "none";
  document.getElementById("askSourceFileInline").style.display = "none";

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
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    showTiming("ask", `Completed in ${elapsed}s`);
    setOutput("askOutput", data.answer);

    if (data.sources && data.sources.length > 0) {
      // Update sources toggle label
      document.getElementById("askSourcesLabel").textContent = `Sources (${data.sources.length})`;

      // Inline source file (first source shown)
      const first = data.sources[0];
      document.getElementById("askSourceFileInline").style.display = "block";
      document.getElementById("askSourceFileInline").innerHTML = `
        <div class="source-file-inline">
          <div class="file-name">📄 ${first.file}</div>
          <div class="file-lines">${first.lines ? "Lines " + first.lines : ""}</div>
        </div>`;

      // Right sidebar sources
      document.getElementById("askSourcesRight").innerHTML = data.sources.map(s => `
        <div class="source-item">
          <div class="source-item-left">
            <span class="source-item-icon">📄</span>
            <div class="source-item-info">
              <span class="source-item-name">${s.file}</span>
              ${s.lines ? `<span class="source-item-lines">Lines ${s.lines}</span>` : ""}
            </div>
          </div>
          <span class="source-item-link">↗</span>
        </div>`).join("");
      document.getElementById("askViewAll").style.display = "flex";

      // Bottom sources list (collapsed)
      document.getElementById("askSources").innerHTML = data.sources
        .map(s => `<div class="source-tag">${s.file}${s.lines ? " · " + s.lines : ""}</div>`)
        .join("");
    } else {
      document.getElementById("askSourcesRight").innerHTML =
        `<div style="font-size:13px;color:var(--text-muted);padding:8px 0;text-align:center;">No sources found.</div>`;
      document.getElementById("askSourcesLabel").textContent = "Sources (0)";
    }
  } catch (e) {
    setError("askOutput", e.message);
    showTiming("ask", "Error");
  } finally {
    setBtn("btnAsk", false);
  }
}

// ─── TOGGLE SOURCES ─────────────────────────────────────────────
function toggleSources(prefix) {
  const list = document.getElementById(prefix + "Sources");
  const toggle = document.getElementById(prefix + "SourcesToggle");
  if (!list) return;
  const isOpen = list.classList.toggle("expanded");
  if (toggle) toggle.classList.toggle("open", isOpen);
}

// ─── AGENT ──────────────────────────────────────────────────────
async function runAgent() {
  const path = getPath();
  const question = document.getElementById("agentQuestion").value.trim();

  if (!path || !question) {
    setError("agentOutput", "Fill in the codebase path and your question.");
    return;
  }

  const t0 = Date.now();
  setLoading("agentOutput", "Agent reasoning... this may take a moment");
  setBtn("btnAgent", true);
  showTiming("agent", "Running...");

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
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    showTiming("agent", `Completed in ${elapsed}s`);
    setOutput("agentOutput", data.answer);
  } catch (e) {
    setError("agentOutput", e.message);
    showTiming("agent", "Error");
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

  const t0 = Date.now();
  setLoading("analyzeOutput", "Analyzing codebase... this may take a minute");
  showTiming("analyze", "Running...");

  const btn = document.getElementById("btnAnalyze");
  btn.disabled = true;
  btn.innerHTML = `<div class="spinner" style="width:12px;height:12px;border-width:2px;display:inline-block;"></div> Analyzing...`;

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
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    showTiming("analyze", `Completed in ${elapsed}s`);

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
    showTiming("analyze", "Error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🔍 RUN ANALYSIS →";
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

  const t0 = Date.now();
  setLoading("issueOutput", "Fetching and analyzing issue...");
  setBtn("btnIssue", true);
  showTiming("issue", "Running...");

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
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    showTiming("issue", `Completed in ${elapsed}s`);
    setOutput("issueOutput", data.analysis || data.error || "No analysis returned.");
  } catch (e) {
    setError("issueOutput", e.message);
    showTiming("issue", "Error");
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

  const t0 = Date.now();
  setLoading("researchOutput", "Searching the web...");
  setBtn("btnResearch", true);
  showTiming("research", "Running...");

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
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    showTiming("research", `Completed in ${elapsed}s`);

    const stackStr = data.stack
      ? `**Detected stack:** ${Array.isArray(data.stack) ? data.stack.join(", ") : JSON.stringify(data.stack)}\n\n---\n\n`
      : "";

    setOutput("researchOutput", stackStr + (data.recommendation || "No recommendation returned."));
  } catch (e) {
    setError("researchOutput", e.message);
    showTiming("research", "Error");
  } finally {
    setBtn("btnResearch", false);
  }
}

// ─── AUTH ──────────────────────────────────────────────────────
function openAuthModal() {
  document.getElementById("authModal").style.display = "flex";
}
function closeAuthModal() {
  document.getElementById("authModal").style.display = "none";
}

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { "Authorization": "Bearer " + token } : {};
}

async function authLogin() {
  const email = document.getElementById("authEmail").value;
  const password = document.getElementById("authPassword").value;
  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (res.ok) {
    localStorage.setItem("token", data.access_token);
    closeAuthModal();
    checkAuth();
  } else {
    document.getElementById("authError").textContent = data.detail || "Login failed";
  }
}

async function authRegister() {
  const email = document.getElementById("authEmail").value;
  const password = document.getElementById("authPassword").value;
  const username = email.split("@")[0];
  const res = await fetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, username })
  });
  const data = await res.json();
  if (res.ok) {
    localStorage.setItem("token", data.access_token);
    closeAuthModal();
    checkAuth();
  } else {
    document.getElementById("authError").textContent = data.detail || "Register failed";
  }
}

function authLogout() {
  localStorage.removeItem("token");
  checkAuth();
}

function checkAuth() {
  const token = localStorage.getItem("token");
  document.getElementById("authLoggedOutBtn").style.display = token ? "none" : "block";
  document.getElementById("authLoggedInBtn").style.display = token ? "flex" : "none";
}

checkAuth();