// src/components/AIPanel.jsx
// AI Panel — 4 features: Explain, Upgrades, Chat, Compare

import { useState, useRef, useEffect } from "react";

// ── Uses same API base as App.jsx ─────────────────────────────────────────────
const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// ─── Shared styles ────────────────────────────────────────────────────────────

const CARD = {
  background: "rgba(255,255,255,0.025)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 16,
  padding: "22px 24px",
  backdropFilter: "blur(16px)",
};

const BTN_PRIMARY = {
  background: "rgba(240,165,0,0.88)",
  border: "none", borderRadius: 10, padding: "11px 20px",
  color: "#0d0b08", fontFamily: "'Syne', sans-serif",
  fontSize: 13, fontWeight: 800, cursor: "pointer",
  transition: "all 0.2s", letterSpacing: 0.5,
};

const BTN_GHOST = {
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 8, padding: "8px 16px", color: "#888",
  fontFamily: "'Space Mono', monospace", fontSize: 11,
  cursor: "pointer", transition: "all 0.2s", letterSpacing: 1,
};

const INPUT = {
  width: "100%", background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 10, padding: "12px 16px", color: "#e8e0d0",
  fontFamily: "'DM Sans', sans-serif", fontSize: 14,
  outline: "none", transition: "border-color 0.2s",
};

const LABEL = {
  fontSize: 11, letterSpacing: 2, color: "#555",
  fontFamily: "'Space Mono', monospace",
  textTransform: "uppercase", marginBottom: 8, display: "block",
};

// ─── Markdown renderer ────────────────────────────────────────────────────────

function MarkdownText({ text }) {
  if (!text) return null;
  const lines = text.split("\n");
  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: "#bbb", lineHeight: 1.8 }}>
      {lines.map((line, i) => {
        if (line.startsWith("## "))  return <div key={i} style={{ fontSize: 15, fontWeight: 700, color: "#e8e0d0", fontFamily: "'Syne', sans-serif", margin: "14px 0 6px" }}>{line.slice(3)}</div>;
        if (line.startsWith("# "))   return <div key={i} style={{ fontSize: 17, fontWeight: 800, color: "#fff", fontFamily: "'Syne', sans-serif", margin: "16px 0 8px" }}>{line.slice(2)}</div>;
        if (line.startsWith("### ")) return <div key={i} style={{ fontSize: 13, fontWeight: 700, color: "#f0a500", fontFamily: "'Space Mono', monospace", margin: "10px 0 4px", letterSpacing: 1 }}>{line.slice(4).toUpperCase()}</div>;
        if (line.startsWith("- ") || line.startsWith("* ")) return <div key={i} style={{ paddingLeft: 14, position: "relative", marginBottom: 3 }}><span style={{ position: "absolute", left: 0, color: "#f0a500" }}>·</span>{line.slice(2)}</div>;
        if (line.match(/^\d+\. /)) return <div key={i} style={{ paddingLeft: 18, position: "relative", marginBottom: 4 }}><span style={{ position: "absolute", left: 0, color: "#f0a500", fontSize: 11 }}>{line.match(/^(\d+)/)[1]}.</span>{line.replace(/^\d+\. /, "")}</div>;
        if (line.startsWith("---") || line.startsWith("===")) return <div key={i} style={{ height: 1, background: "rgba(255,255,255,0.06)", margin: "12px 0" }} />;
        if (line.trim() === "") return <div key={i} style={{ height: 8 }} />;
        const parts = line.split(/(\*\*[^*]+\*\*)/g);
        return (
          <div key={i} style={{ marginBottom: 2 }}>
            {parts.map((p, j) =>
              p.startsWith("**") ? <strong key={j} style={{ color: "#e8e0d0", fontWeight: 600 }}>{p.slice(2, -2)}</strong> : p
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Spinner ──────────────────────────────────────────────────────────────────

function Spinner({ label = "Thinking..." }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#f0a500", fontFamily: "'Space Mono', monospace", fontSize: 12, padding: "16px 0" }}>
      <div style={{ width: 14, height: 14, border: "2px solid rgba(240,165,0,0.2)", borderTop: "2px solid #f0a500", borderRadius: "50%", animation: "spin 0.8s linear infinite", flexShrink: 0 }} />
      {label}
    </div>
  );
}

// ─── Error box ────────────────────────────────────────────────────────────────

function ErrorBox({ message }) {
  return (
    <div style={{ color: "#ef4444", fontFamily: "'DM Sans', sans-serif", fontSize: 13, padding: "10px 14px", background: "rgba(239,68,68,0.08)", borderRadius: 8, border: "1px solid rgba(239,68,68,0.2)", marginTop: 8 }}>
      ⚠️ {message}
    </div>
  );
}

// ─── Tabs ─────────────────────────────────────────────────────────────────────

const TABS = [
  { id: "explain",  label: "Explain",  icon: "💡" },
  { id: "chat",     label: "Chat",     icon: "💬" },
  { id: "upgrades", label: "Upgrades", icon: "⬆️" },
  { id: "compare",  label: "Compare",  icon: "⚖️" },
];

// ─── Explain Tab ──────────────────────────────────────────────────────────────

function ExplainTab({ build, intent, budget, resolution }) {
  const [result,  setResult]  = useState("");
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const handleExplain = async () => {
    setLoading(true); setError(""); setResult("");
    try {
      const res  = await fetch(`${API}/api/ai/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ build, intent, budget, resolution }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setResult(data.explanation);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <p style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: "#666", marginBottom: 16, lineHeight: 1.6 }}>
        Get a detailed explanation of why each component was selected for your specific use case and budget.
      </p>

      {!result && !loading && (
        <button onClick={handleExplain} style={BTN_PRIMARY}>💡 Explain This Build</button>
      )}
      {loading && <Spinner label="Analyzing your build..." />}
      {error   && <ErrorBox message={error} />}
      {result  && (
        <div>
          <MarkdownText text={result} />
          <button onClick={() => setResult("")} style={{ ...BTN_GHOST, marginTop: 16, fontSize: 10 }}>
            ↺ Regenerate
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Chat Tab ─────────────────────────────────────────────────────────────────

function ChatTab({ build, intent, budget, resolution }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: `Hi! I'm here to answer questions about your **${intent}** build. Ask me anything — compatibility, performance, alternatives, or upgrades!` }
  ]);
  const [input,   setInput]   = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef             = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");

    const newMessages = [...messages, { role: "user", content: msg }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const res  = await fetch(`${API}/api/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: msg, build, intent, budget, resolution,
          history: messages.slice(1),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setMessages([...newMessages, { role: "assistant", content: data.reply }]);
    } catch (e) {
      setMessages([...newMessages, { role: "assistant", content: `Sorry, something went wrong: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      <div style={{ maxHeight: 360, overflowY: "auto", paddingRight: 4, marginBottom: 14 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start", marginBottom: 10 }}>
            <div style={{
              maxWidth: "85%",
              background: m.role === "user" ? "rgba(240,165,0,0.15)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${m.role === "user" ? "rgba(240,165,0,0.25)" : "rgba(255,255,255,0.07)"}`,
              borderRadius: m.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
              padding: "10px 14px",
            }}>
              {m.role === "assistant"
                ? <MarkdownText text={m.content} />
                : <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: "#f0c040" }}>{m.content}</div>
              }
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 10 }}>
            <div style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "14px 14px 14px 4px", padding: "10px 14px" }}>
              <Spinner label="Typing..." />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
          placeholder="Ask anything about this build..."
          style={{ ...INPUT, flex: 1 }}
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          style={{ ...BTN_PRIMARY, padding: "11px 16px", opacity: (!input.trim() || loading) ? 0.5 : 1 }}
        >
          ➤
        </button>
      </div>
    </div>
  );
}

// ─── Upgrades Tab ─────────────────────────────────────────────────────────────

const UPGRADE_FIELDS = [
  { key: "cpu",         label: "CPU"         },
  { key: "gpu",         label: "GPU"         },
  { key: "ram",         label: "RAM"         },
  { key: "motherboard", label: "Motherboard" },
  { key: "storage",     label: "Storage"     },
  { key: "psu",         label: "PSU"         },
];

function UpgradesTab() {
  const [specs,   setSpecs]   = useState({});
  const [budget,  setBudget]  = useState(20000);
  const [useCase, setUseCase] = useState("Gaming");
  const [result,  setResult]  = useState("");
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const handleSubmit = async () => {
    const filled = Object.fromEntries(Object.entries(specs).filter(([, v]) => v?.trim()));
    if (!Object.keys(filled).length) { setError("Enter at least one current component"); return; }
    setLoading(true); setError(""); setResult("");
    try {
      const res  = await fetch(`${API}/api/ai/upgrades`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_specs: filled, budget, use_case: useCase }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setResult(data.suggestions);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {!result ? (
        <>
          <p style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: "#666", marginBottom: 18, lineHeight: 1.6 }}>
            Enter your current PC specs and upgrade budget. AI will tell you exactly what to upgrade first.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
            {UPGRADE_FIELDS.map(({ key, label }) => (
              <div key={key}>
                <label style={LABEL}>{label}</label>
                <input
                  value={specs[key] || ""}
                  onChange={(e) => setSpecs((s) => ({ ...s, [key]: e.target.value }))}
                  placeholder={`e.g. ${key === "cpu" ? "i5-9400F" : key === "gpu" ? "GTX 1060 6GB" : key === "ram" ? "16GB DDR4" : "..."}`}
                  style={{ ...INPUT, fontSize: 12, padding: "10px 12px" }}
                />
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 18 }}>
            <div>
              <label style={LABEL}>Upgrade Budget</label>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <input type="range" min="5000" max="100000" step="1000"
                  value={budget} onChange={(e) => setBudget(Number(e.target.value))}
                  style={{ flex: 1, accentColor: "#f0a500" }}
                />
                <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 12, color: "#f0c040", whiteSpace: "nowrap" }}>
                  ₹{Number(budget).toLocaleString("en-IN")}
                </span>
              </div>
            </div>
            <div>
              <label style={LABEL}>Use Case</label>
              <select value={useCase} onChange={(e) => setUseCase(e.target.value)}
                style={{ ...INPUT, fontSize: 12, padding: "10px 12px" }}>
                {["Gaming","FPS / Competitive","Video Editing","3D / CAD","Streaming","Programming","Office / Study"].map((u) => (
                  <option key={u} value={u} style={{ background: "#1a1814" }}>{u}</option>
                ))}
              </select>
            </div>
          </div>

          {error && <ErrorBox message={error} />}

          <button onClick={handleSubmit} disabled={loading}
            style={{ ...BTN_PRIMARY, opacity: loading ? 0.6 : 1, marginTop: 8 }}>
            ⬆️ Suggest Upgrades
          </button>
          {loading && <Spinner label="Analyzing upgrade options..." />}
        </>
      ) : (
        <div>
          <MarkdownText text={result} />
          <button onClick={() => setResult("")} style={{ ...BTN_GHOST, marginTop: 16, fontSize: 10 }}>
            ← Back
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Compare Tab ──────────────────────────────────────────────────────────────

function CompareTab({ build, intent, budget, resolution }) {
  const [buildB,     setBuildB]     = useState(null);
  const [budgetB,    setBudgetB]    = useState(Math.round(budget * 1.3 / 5000) * 5000);
  const [result,     setResult]     = useState("");
  const [loading,    setLoading]    = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error,      setError]      = useState("");

  const handleGenerate = async () => {
    setGenerating(true); setError("");
    try {
      const res  = await fetch(`${API}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: intent, budget: budgetB, resolution }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setBuildB(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleCompare = async () => {
    if (!buildB) return;
    setLoading(true); setError(""); setResult("");
    try {
      const res  = await fetch(`${API}/api/ai/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          build_a: { ...build, budget },
          build_b: { ...buildB.build, budget: budgetB },
          intent, resolution,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setResult(data.comparison);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <MarkdownText text={result} />
        <button onClick={() => { setResult(""); setBuildB(null); }}
          style={{ ...BTN_GHOST, marginTop: 16, fontSize: 10 }}>← Back</button>
      </div>
    );
  }

  return (
    <div>
      <p style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: "#666", marginBottom: 18, lineHeight: 1.6 }}>
        Compare your current build against a different budget to see what you gain or lose.
      </p>

      {/* Build A */}
      <div style={{ background: "rgba(240,165,0,0.06)", border: "1px solid rgba(240,165,0,0.15)", borderRadius: 10, padding: "12px 16px", marginBottom: 12 }}>
        <div style={{ fontSize: 10, color: "#f0a500", fontFamily: "'Space Mono', monospace", letterSpacing: 2, marginBottom: 4 }}>BUILD A (CURRENT)</div>
        <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: "#e8e0d0" }}>
          {intent} · ₹{Number(budget).toLocaleString("en-IN")} · {resolution}
        </div>
      </div>

      {/* Build B */}
      <div style={{ background: "rgba(124,106,247,0.06)", border: "1px solid rgba(124,106,247,0.15)", borderRadius: 10, padding: "14px 16px", marginBottom: 16 }}>
        <div style={{ fontSize: 10, color: "#7c6af7", fontFamily: "'Space Mono', monospace", letterSpacing: 2, marginBottom: 10 }}>BUILD B (COMPARISON)</div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
          <input type="range" min="20000" max="400000" step="5000"
            value={budgetB}
            onChange={(e) => { setBudgetB(Number(e.target.value)); setBuildB(null); setResult(""); }}
            style={{ flex: 1, accentColor: "#7c6af7" }}
          />
          <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 12, color: "#7c6af7", whiteSpace: "nowrap" }}>
            ₹{Number(budgetB).toLocaleString("en-IN")}
          </span>
        </div>
        {!buildB ? (
          <button onClick={handleGenerate} disabled={generating}
            style={{ ...BTN_GHOST, borderColor: "rgba(124,106,247,0.3)", color: "#7c6af7", opacity: generating ? 0.6 : 1 }}>
            {generating ? "Generating..." : "⚡ Generate Build B"}
          </button>
        ) : (
          <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 12, color: "#64dc82" }}>
            ✓ Build B ready · ₹{Number(buildB.build?.total_price || 0).toLocaleString("en-IN")}
          </div>
        )}
        {generating && <Spinner label="Building comparison..." />}
      </div>

      {error && <ErrorBox message={error} />}

      <button onClick={handleCompare} disabled={!buildB || loading}
        style={{ ...BTN_PRIMARY, opacity: (!buildB || loading) ? 0.5 : 1 }}>
        ⚖️ Compare Builds
      </button>
      {loading && <Spinner label="Comparing builds with AI..." />}
    </div>
  );
}

// ─── Main AIPanel ─────────────────────────────────────────────────────────────

export default function AIPanel({ result }) {
  const [activeTab, setActiveTab] = useState("explain");

  const build      = result?.build || {};
  const intent     = result?.intent || "Gaming";
  const budget     = result?.build?.total_price || 80000;
  const resolution = result?.resolution || "1080p";

  if (!result) return null;

  return (
    <div style={{ marginTop: 24 }}>
      <style>{`
        @keyframes spin    { to { transform: rotate(360deg); } }
        @keyframes fadeIn  { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        .ai-tab:hover { color: #e8e0d0 !important; border-color: rgba(255,255,255,0.15) !important; }
      `}</style>

      {/* Section header */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
        <div style={{ width: 1, height: 20, background: "rgba(240,165,0,0.4)" }} />
        <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 11, letterSpacing: 3, color: "#f0a500", textTransform: "uppercase" }}>
          AI Assistant
        </div>
        <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.05)" }} />
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
        {TABS.map((tab) => (
          <button key={tab.id} className="ai-tab"
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: activeTab === tab.id ? "rgba(240,165,0,0.12)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${activeTab === tab.id ? "rgba(240,165,0,0.4)" : "rgba(255,255,255,0.07)"}`,
              borderRadius: 8, padding: "7px 14px",
              color: activeTab === tab.id ? "#f0c040" : "#555",
              fontFamily: "'Space Mono', monospace", fontSize: 11,
              cursor: "pointer", transition: "all 0.2s",
              display: "flex", alignItems: "center", gap: 6, letterSpacing: 0.5,
            }}
          >
            <span>{tab.icon}</span>{tab.label}
          </button>
        ))}
      </div>

      {/* Panel */}
      <div style={{ ...CARD, animation: "fadeIn 0.3s ease" }}>
        {activeTab === "explain"  && <ExplainTab  build={build} intent={intent} budget={budget} resolution={resolution} />}
        {activeTab === "chat"     && <ChatTab     build={build} intent={intent} budget={budget} resolution={resolution} />}
        {activeTab === "upgrades" && <UpgradesTab />}
        {activeTab === "compare"  && <CompareTab  build={build} intent={intent} budget={budget} resolution={resolution} />}
      </div>
    </div>
  );
}