import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { apiKey, login, loading, error } = useAuth();
  const [key, setKey] = useState("");
  const navigate = useNavigate();

  if (apiKey) return <Navigate to="/shows" replace />;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await login(key.trim());
      navigate("/shows");
    } catch {
      // error already surfaced via auth context
    }
  }

  return (
    <div className="login-page">
      <form className="login-form" onSubmit={handleSubmit}>
        <h1>Peblo TV Mini · CMS</h1>
        <p>Enter your API key to continue.</p>
        <input
          type="password"
          placeholder="API key"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          autoFocus
        />
        <button type="submit" disabled={loading || !key.trim()}>
          {loading ? "Checking..." : "Log in"}
        </button>
        {error && <div className="login-error">{error}</div>}
      </form>
    </div>
  );
}