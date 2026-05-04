// src/pages/AuthPage.jsx
// Login + Register page with tab switching

import { useState } from "react";
import { useAuth } from "../context/AuthContext";

const INPUT_STYLE = {
  width: "100%",
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 10,
  padding: "13px 16px",
  color: "#e8e0d0",
  fontFamily: "'DM Sans', sans-serif",
  fontSize: 14,
  transition: "all 0.2s",
  outline: "none",
};

function Field({ label, type = "text", value, onChange, placeholder, error }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, letterSpacing: 2, color: "#555", fontFamily: "'Space Mono', monospace", textTransform: "uppercase", marginBottom: 8 }}>
        {label}
      </div>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          ...INPUT_STYLE,
          borderColor: error ? "rgba(239,68,68,0.5)" : focused ? "rgba(240,165,0,0.5)" : "rgba(255,255,255,0.1)",
          boxShadow: focused ? "0 0 0 3px rgba(240,165,0,0.08)" : error ? "0 0 0 3px rgba(239,68,68,0.08)" : "none",
        }}
      />
      {error && (
        <div style={{ fontSize: 12, color: "#ef4444", fontFamily: "'DM Sans', sans-serif", marginTop: 5 }}>
          {error}
        </div>
      )}
    </div>
  );
}

export default function AuthPage({ onSuccess }) {
  const { login, register } = useAuth();
  const [tab, setTab]         = useState("login");   // "login" | "register"
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  // Login form
  const [loginEmail, setLoginEmail]       = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form
  const [regEmail, setRegEmail]       = useState("");
  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirm, setRegConfirm]   = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const validateRegister = () => {
    const errs = {};
    if (!regEmail.includes("@")) errs.email = "Enter a valid email";
    if (regUsername.length < 3) errs.username = "At least 3 characters";
    if (!/^[a-zA-Z0-9_]+$/.test(regUsername)) errs.username = "Letters, numbers, underscores only";
    if (regPassword.length < 8) errs.password = "At least 8 characters";
    if (regPassword !== regConfirm) errs.confirm = "Passwords don't match";
    return errs;
  };

  const handleLogin = async (e) => {
    e?.preventDefault();
    if (!loginEmail || !loginPassword) return;
    setLoading(true);
    setError("");
    try {
      await login(loginEmail, loginPassword);
      onSuccess?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e?.preventDefault();
    const errs = validateRegister();
    if (Object.keys(errs).length) { setFieldErrors(errs); return; }
    setFieldErrors({});
    setLoading(true);
    setError("");
    try {
      await register(regEmail, regUsername, regPassword);
      onSuccess?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0d0b08",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
      fontFamily: "'DM Sans', sans-serif",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap');
        @keyframes fadeUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
        .auth-btn:hover:not(:disabled) { background: #f0c040 !important; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(240,165,0,0.3) !important; }
        .tab-btn:hover { color: #e8e0d0 !important; }
        .social-btn:hover { border-color: rgba(255,255,255,0.2) !important; background: rgba(255,255,255,0.06) !important; }
      `}</style>

      {/* Background glow */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none" }}>
        <div style={{ position: "absolute", width: 400, height: 400, top: "20%", left: "50%", transform: "translateX(-50%)", background: "rgba(240,140,0,0.06)", borderRadius: "50%", filter: "blur(80px)" }} />
      </div>

      <div style={{ width: "100%", maxWidth: 420, animation: "fadeUp 0.5s ease" }}>

        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 28, marginBottom: 8 }}>⚡</div>
          <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 22, letterSpacing: 2, color: "#fff" }}>RIGCRAFT</div>
          <div style={{ fontSize: 12, color: "#444", fontFamily: "'Space Mono', monospace", marginTop: 4 }}>PC Build Recommendation Engine</div>
        </div>

        {/* Card */}
        <div style={{
          background: "rgba(255,255,255,0.025)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 20,
          padding: "28px 28px",
          backdropFilter: "blur(16px)",
        }}>

          {/* Tabs */}
          <div style={{ display: "flex", background: "rgba(255,255,255,0.04)", borderRadius: 10, padding: 3, marginBottom: 26 }}>
            {["login", "register"].map((t) => (
              <button
                key={t}
                className="tab-btn"
                onClick={() => { setTab(t); setError(""); setFieldErrors({}); }}
                style={{
                  flex: 1,
                  background: tab === t ? "rgba(240,165,0,0.15)" : "none",
                  border: tab === t ? "1px solid rgba(240,165,0,0.3)" : "1px solid transparent",
                  borderRadius: 8,
                  padding: "9px",
                  color: tab === t ? "#f0c040" : "#555",
                  fontFamily: "'Space Mono', monospace",
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: "pointer",
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  transition: "all 0.2s",
                }}
              >
                {t === "login" ? "Sign In" : "Register"}
              </button>
            ))}
          </div>

          {/* Error banner */}
          {error && (
            <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 8, padding: "10px 14px", color: "#ef4444", fontSize: 13, marginBottom: 18 }}>
              ⚠️ {error}
            </div>
          )}

          {/* ── Login Form ── */}
          {tab === "login" && (
            <div>
              <Field label="Email" type="email" value={loginEmail} onChange={setLoginEmail} placeholder="you@example.com" />
              <Field label="Password" type="password" value={loginPassword} onChange={setLoginPassword} placeholder="••••••••" />

              <button
                className="auth-btn"
                onClick={handleLogin}
                disabled={loading || !loginEmail || !loginPassword}
                style={{
                  width: "100%", marginTop: 8,
                  background: "rgba(240,165,0,0.88)",
                  border: "none", borderRadius: 10, padding: "14px",
                  color: "#0d0b08", fontFamily: "'Syne', sans-serif",
                  fontSize: 14, fontWeight: 800, cursor: loading ? "not-allowed" : "pointer",
                  transition: "all 0.25s", letterSpacing: 1,
                  opacity: loading ? 0.6 : 1,
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                }}
              >
                {loading ? (
                  <><div style={{ width: 14, height: 14, border: "2px solid rgba(0,0,0,0.2)", borderTop: "2px solid #0d0b08", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />Signing in...</>
                ) : "Sign In →"}
              </button>

              <div style={{ textAlign: "center", marginTop: 16, fontSize: 12, color: "#444", fontFamily: "'DM Sans', sans-serif" }}>
                Don't have an account?{" "}
                <span onClick={() => setTab("register")} style={{ color: "#f0a500", cursor: "pointer" }}>
                  Register
                </span>
              </div>
            </div>
          )}

          {/* ── Register Form ── */}
          {tab === "register" && (
            <div>
              <Field label="Email" type="email" value={regEmail} onChange={setRegEmail} placeholder="you@example.com" error={fieldErrors.email} />
              <Field label="Username" value={regUsername} onChange={setRegUsername} placeholder="coolbuilder99" error={fieldErrors.username} />
              <Field label="Password" type="password" value={regPassword} onChange={setRegPassword} placeholder="Min 8 characters" error={fieldErrors.password} />
              <Field label="Confirm Password" type="password" value={regConfirm} onChange={setRegConfirm} placeholder="Repeat password" error={fieldErrors.confirm} />

              {/* Password strength */}
              {regPassword.length > 0 && (
                <div style={{ marginBottom: 16, marginTop: -8 }}>
                  <div style={{ display: "flex", gap: 4 }}>
                    {[1, 2, 3, 4].map((level) => {
                      const strength = Math.min(
                        4,
                        (regPassword.length >= 8 ? 1 : 0) +
                        (/[A-Z]/.test(regPassword) ? 1 : 0) +
                        (/[0-9]/.test(regPassword) ? 1 : 0) +
                        (/[^A-Za-z0-9]/.test(regPassword) ? 1 : 0)
                      );
                      const colors = ["#ef4444", "#f97316", "#eab308", "#22c55e"];
                      return (
                        <div key={level} style={{ flex: 1, height: 3, borderRadius: 2, background: level <= strength ? colors[strength - 1] : "rgba(255,255,255,0.06)", transition: "background 0.3s" }} />
                      );
                    })}
                  </div>
                  <div style={{ fontSize: 11, color: "#555", marginTop: 4, fontFamily: "'DM Sans', sans-serif" }}>
                    {["", "Weak", "Fair", "Good", "Strong"][Math.min(4, (regPassword.length >= 8 ? 1 : 0) + (/[A-Z]/.test(regPassword) ? 1 : 0) + (/[0-9]/.test(regPassword) ? 1 : 0) + (/[^A-Za-z0-9]/.test(regPassword) ? 1 : 0))]} password
                  </div>
                </div>
              )}

              <button
                className="auth-btn"
                onClick={handleRegister}
                disabled={loading}
                style={{
                  width: "100%", marginTop: 4,
                  background: "rgba(240,165,0,0.88)",
                  border: "none", borderRadius: 10, padding: "14px",
                  color: "#0d0b08", fontFamily: "'Syne', sans-serif",
                  fontSize: 14, fontWeight: 800, cursor: loading ? "not-allowed" : "pointer",
                  transition: "all 0.25s", letterSpacing: 1,
                  opacity: loading ? 0.6 : 1,
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                }}
              >
                {loading ? (
                  <><div style={{ width: 14, height: 14, border: "2px solid rgba(0,0,0,0.2)", borderTop: "2px solid #0d0b08", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />Creating account...</>
                ) : "Create Account →"}
              </button>

              <div style={{ textAlign: "center", marginTop: 16, fontSize: 12, color: "#444", fontFamily: "'DM Sans', sans-serif" }}>
                Already have an account?{" "}
                <span onClick={() => setTab("login")} style={{ color: "#f0a500", cursor: "pointer" }}>
                  Sign in
                </span>
              </div>
            </div>
          )}
        </div>

        <div style={{ textAlign: "center", marginTop: 24, color: "#2a2a2a", fontFamily: "'Space Mono', monospace", fontSize: 10, letterSpacing: 2 }}>
          RIGCRAFT · ALL PRICES IN INR
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}