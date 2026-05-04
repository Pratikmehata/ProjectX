// src/pages/AuthPage.jsx
import { useState } from "react";
import styled from "styled-components";
import { useAuth } from "../context/AuthContext";

const AuthPage = ({ onSuccess }) => {
  const { login, register } = useAuth();
  const [activeTab, setActiveTab] = useState("login"); // "login" | "register"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Login form
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form
  const [regEmail, setRegEmail] = useState("");
  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirm, setRegConfirm] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  // ─── Validation ─────────────────────────────────────────
  const validateRegister = () => {
    const errs = {};
    if (!regEmail.includes("@")) errs.email = "Enter a valid email";
    if (regUsername.length < 3) errs.username = "At least 3 characters";
    if (!/^[a-zA-Z0-9_]+$/.test(regUsername))
      errs.username = "Letters, numbers, underscores only";
    if (regPassword.length < 8) errs.password = "At least 8 characters";
    if (regPassword !== regConfirm) errs.confirm = "Passwords don't match";
    return errs;
  };

  // ─── Handlers ───────────────────────────────────────────
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
    if (Object.keys(errs).length) {
      setFieldErrors(errs);
      return;
    }
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

  // ─── Password strength helper ───────────────────────────
  const getStrength = () => {
    let score = 0;
    if (regPassword.length >= 8) score++;
    if (/[A-Z]/.test(regPassword)) score++;
    if (/[0-9]/.test(regPassword)) score++;
    if (/[^A-Za-z0-9]/.test(regPassword)) score++;
    return Math.min(4, score);
  };

  const strengthLabels = ["", "Weak", "Fair", "Good", "Strong"];
  const strengthColors = ["", "#ef4444", "#f97316", "#eab308", "#22c55e"];

  return (
    <StyledWrapper>
      <div className="card">
        <div className="card2">
          <form className="form" onSubmit={(e) => e.preventDefault()}>
            <p id="heading">RIGCRAFT</p>

            {/* Custom Neon Tabs */}
            <div className="tab-container">
              <button
                type="button"
                className={`tab-btn ${activeTab === "login" ? "active" : ""}`}
                onClick={() => {
                  setActiveTab("login");
                  setError("");
                  setFieldErrors({});
                }}
              >
                Login
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === "register" ? "active" : ""}`}
                onClick={() => {
                  setActiveTab("register");
                  setError("");
                  setFieldErrors({});
                }}
              >
                Register
              </button>
            </div>

            {/* Error message */}
            {error && (
              <div className="error-message">
                <span>⚠️</span> {error}
              </div>
            )}

            {/* ========= LOGIN FORM ========= */}
            {activeTab === "login" && (
              <>
                <div className="field">
                  <svg
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    height={16}
                    width={16}
                    xmlns="http://www.w3.org/2000/svg"
                    className="input-icon"
                  >
                    <path d="M13.106 7.222c0-2.967-2.249-5.032-5.482-5.032-3.35 0-5.646 2.318-5.646 5.702 0 3.493 2.235 5.708 5.762 5.708.862 0 1.689-.123 2.304-.335v-.862c-.43.199-1.354.328-2.29.328-2.926 0-4.813-1.88-4.813-4.798 0-2.844 1.921-4.881 4.594-4.881 2.735 0 4.608 1.688 4.608 4.156 0 1.682-.554 2.769-1.416 2.769-.492 0-.772-.28-.772-.76V5.206H8.923v.834h-.11c-.266-.595-.881-.964-1.6-.964-1.4 0-2.378 1.162-2.378 2.823 0 1.737.957 2.906 2.379 2.906.8 0 1.415-.39 1.709-1.087h.11c.081.67.703 1.148 1.503 1.148 1.572 0 2.57-1.415 2.57-3.643zm-7.177.704c0-1.197.54-1.907 1.456-1.907.93 0 1.524.738 1.524 1.907S8.308 9.84 7.371 9.84c-.895 0-1.442-.725-1.442-1.914z" />
                  </svg>
                  <input
                    type="email"
                    className="input-field"
                    placeholder="Email"
                    autoComplete="off"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                  />
                </div>

                <div className="field">
                  <svg
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    height={16}
                    width={16}
                    xmlns="http://www.w3.org/2000/svg"
                    className="input-icon"
                  >
                    <path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z" />
                  </svg>
                  <input
                    type="password"
                    className="input-field"
                    placeholder="Password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                  />
                </div>

                <div className="btn">
                  <button
                    type="button"
                    className="button1"
                    onClick={handleLogin}
                    disabled={loading || !loginEmail || !loginPassword}
                  >
                    {loading ? "Signing in..." : "Login"}
                  </button>
                </div>

                <button type="button" className="button3">
                  Forgot Password
                </button>
              </>
            )}

            {/* ========= REGISTER FORM ========= */}
            {activeTab === "register" && (
              <>
                <div className="field">
                  <svg
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    height={16}
                    width={16}
                    xmlns="http://www.w3.org/2000/svg"
                    className="input-icon"
                  >
                    <path d="M13.106 7.222c0-2.967-2.249-5.032-5.482-5.032-3.35 0-5.646 2.318-5.646 5.702 0 3.493 2.235 5.708 5.762 5.708.862 0 1.689-.123 2.304-.335v-.862c-.43.199-1.354.328-2.29.328-2.926 0-4.813-1.88-4.813-4.798 0-2.844 1.921-4.881 4.594-4.881 2.735 0 4.608 1.688 4.608 4.156 0 1.682-.554 2.769-1.416 2.769-.492 0-.772-.28-.772-.76V5.206H8.923v.834h-.11c-.266-.595-.881-.964-1.6-.964-1.4 0-2.378 1.162-2.378 2.823 0 1.737.957 2.906 2.379 2.906.8 0 1.415-.39 1.709-1.087h.11c.081.67.703 1.148 1.503 1.148 1.572 0 2.57-1.415 2.57-3.643zm-7.177.704c0-1.197.54-1.907 1.456-1.907.93 0 1.524.738 1.524 1.907S8.308 9.84 7.371 9.84c-.895 0-1.442-.725-1.442-1.914z" />
                  </svg>
                  <input
                    type="email"
                    className="input-field"
                    placeholder="Email"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                  />
                </div>
                {fieldErrors.email && (
                  <div className="field-error">{fieldErrors.email}</div>
                )}

                <div className="field">
                  <svg
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    height={16}
                    width={16}
                    xmlns="http://www.w3.org/2000/svg"
                    className="input-icon"
                  >
                    <path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z" />
                  </svg>
                  <input
                    type="text"
                    className="input-field"
                    placeholder="Username"
                    value={regUsername}
                    onChange={(e) => setRegUsername(e.target.value)}
                  />
                </div>
                {fieldErrors.username && (
                  <div className="field-error">{fieldErrors.username}</div>
                )}

                <div className="field">
                  <svg
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    height={16}
                    width={16}
                    xmlns="http://www.w3.org/2000/svg"
                    className="input-icon"
                  >
                    <path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z" />
                  </svg>
                  <input
                    type="password"
                    className="input-field"
                    placeholder="Password (min 8 chars)"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                  />
                </div>
                {fieldErrors.password && (
                  <div className="field-error">{fieldErrors.password}</div>
                )}

                <div className="field">
                  <svg
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    height={16}
                    width={16}
                    xmlns="http://www.w3.org/2000/svg"
                    className="input-icon"
                  >
                    <path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z" />
                  </svg>
                  <input
                    type="password"
                    className="input-field"
                    placeholder="Confirm Password"
                    value={regConfirm}
                    onChange={(e) => setRegConfirm(e.target.value)}
                  />
                </div>
                {fieldErrors.confirm && (
                  <div className="field-error">{fieldErrors.confirm}</div>
                )}

                {/* Password strength indicator */}
                {regPassword.length > 0 && (
                  <div className="strength-bars">
                    <div className="strength-container">
                      {[1, 2, 3, 4].map((level) => {
                        const strength = getStrength();
                        return (
                          <div
                            key={level}
                            style={{
                              flex: 1,
                              height: 4,
                              borderRadius: 2,
                              background:
                                level <= strength
                                  ? strengthColors[strength]
                                  : "rgba(255,255,255,0.1)",
                              transition: "background 0.2s",
                            }}
                          />
                        );
                      })}
                    </div>
                    <div className="strength-text">
                      {strengthLabels[getStrength()]} password
                    </div>
                  </div>
                )}

                <div className="btn">
                  <button
                    type="button"
                    className="button1"
                    onClick={handleRegister}
                    disabled={loading}
                  >
                    {loading ? "Creating account..." : "Sign Up"}
                  </button>
                </div>
              </>
            )}
          </form>
        </div>
      </div>
    </StyledWrapper>
  );
};

// ──────────────────────────────────────────────────────────
// Styled Components (neon theme from original Form)
// ──────────────────────────────────────────────────────────
const StyledWrapper = styled.div`
  .form {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding-left: 2em;
    padding-right: 2em;
    padding-bottom: 0.4em;
    background-color: #171717;
    border-radius: 20px;
  }

  #heading {
    text-align: center;
    margin: 1em 0 0.5em 0;
    color: rgb(0, 255, 200);
    font-size: 1.5em;
    font-weight: bold;
    letter-spacing: 2px;
  }

  .tab-container {
    display: flex;
    gap: 12px;
    margin: 0.5em 0 1em;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 40px;
    padding: 4px;
  }

  .tab-btn {
    flex: 1;
    background: transparent;
    border: none;
    padding: 8px 0;
    border-radius: 40px;
    color: #888;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
  }

  .tab-btn.active {
    background: rgb(0, 255, 200);
    color: #171717;
    box-shadow: 0 0 8px rgba(0, 255, 200, 0.4);
  }

  .error-message {
    background: rgba(239, 68, 68, 0.15);
    border-left: 3px solid #ef4444;
    color: #ef4444;
    font-size: 0.8rem;
    padding: 8px 12px;
    border-radius: 8px;
    margin: 10px 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .field {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5em;
    border-radius: 25px;
    padding: 0.6em;
    border: none;
    outline: none;
    color: white;
    background-color: #171717;
    box-shadow: inset 2px 5px 10px rgb(5, 5, 5);
  }

  .input-icon {
    height: 1.3em;
    width: 1.3em;
    fill: rgb(0, 255, 200);
  }

  .input-field {
    background: none;
    border: none;
    outline: none;
    width: 100%;
    color: rgb(0, 255, 200);
  }

  .input-field::placeholder {
    color: rgba(0, 255, 200, 0.5);
  }

  .field-error {
    color: #ef4444;
    font-size: 0.7rem;
    margin-top: -6px;
    margin-bottom: 4px;
    margin-left: 12px;
  }

  .strength-bars {
    margin: 4px 8px 8px 8px;
  }

  .strength-container {
    display: flex;
    gap: 6px;
    margin-bottom: 4px;
  }

  .strength-text {
    font-size: 0.7rem;
    color: #aaa;
    text-align: right;
  }

  .form .btn {
    display: flex;
    justify-content: center;
    flex-direction: row;
    margin-top: 1em;
    margin-bottom: 0.5em;
  }

  .button1 {
    padding: 0.5em 1.5em;
    border-radius: 5px;
    border: none;
    outline: none;
    transition: 0.4s ease-in-out;
    background-image: linear-gradient(163deg, #00ff75 0%, #3700ff 100%);
    color: rgb(0, 0, 0);
    font-weight: bold;
    cursor: pointer;
    width: 100%;
  }

  .button1:hover:not(:disabled) {
    background-image: linear-gradient(163deg, #00642f 0%, #13034b 100%);
    color: rgb(0, 255, 200);
    transform: scale(0.98);
  }

  .button1:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .button2 {
    padding: 0.5em;
    padding-left: 2.3em;
    padding-right: 2.3em;
    border-radius: 5px;
    border: none;
    outline: none;
    transition: 0.4s ease-in-out;
    background-image: linear-gradient(163deg, #00ff75 0%, #3700ff 100%);
    color: rgb(0, 0, 0);
  }

  .button2:hover {
    background-image: linear-gradient(163deg, #00642f 0%, #13034b 100%);
    color: rgb(0, 255, 200);
  }

  .button3 {
    margin-bottom: 1.5em;
    padding: 0.5em;
    border-radius: 5px;
    border: none;
    outline: none;
    transition: 0.4s ease-in-out;
    background-image: linear-gradient(163deg, #00ff75 0%, #3700ff 100%);
    color: rgb(0, 0, 0);
    cursor: pointer;
    font-size: 0.8rem;
  }

  .button3:hover {
    background-image: linear-gradient(163deg, #a00000fa 0%, #d10050 100%);
    color: rgb(255, 255, 255);
  }

  .card {
    background-image: linear-gradient(163deg, #00ff75 0%, #3700ff 100%);
    border-radius: 22px;
    transition: all 0.3s;
  }

  .card2 {
    border-radius: 0;
    transition: all 0.2s;
  }

  .card2:hover {
    transform: scale(0.98);
    border-radius: 20px;
  }

  .card:hover {
    box-shadow: 0px 0px 30px 1px rgba(0, 255, 117, 0.3);
  }
`;

export default AuthPage;