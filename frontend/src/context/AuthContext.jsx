// src/context/AuthContext.jsx
import { createContext, useContext, useState } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  // Mock login – replace with real API call
  const login = async (email, password) => {
    setLoading(true);
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 500));
    // Dummy validation
    if (email && password) {
      setUser({ email, username: email.split('@')[0] });
    } else {
      throw new Error("Invalid credentials");
    }
    setLoading(false);
  };

  // Mock register – replace with real API call
  const register = async (email, username, password) => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 500));
    // Dummy validation
    if (email && username && password) {
      setUser({ email, username });
    } else {
      throw new Error("Registration failed");
    }
    setLoading(false);
  };

  const logout = () => {
    setUser(null);
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}