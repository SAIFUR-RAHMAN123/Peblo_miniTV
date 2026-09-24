import { NavLink, Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Layout() {
  const { apiKey, role, logout } = useAuth();

  if (!apiKey) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-left">
          <span className="app-title">Peblo TV Mini · CMS</span>
          <nav>
            <NavLink to="/shows" className={({ isActive }) => (isActive ? "active" : "")}>
              Shows
            </NavLink>
            <NavLink to="/publish" className={({ isActive }) => (isActive ? "active" : "")}>
              Publish
            </NavLink>
          </nav>
        </div>
        <div className="app-header-right">
          {role && <span className={`role-badge role-${role}`}>{role}</span>}
          <button className="link-button" onClick={logout}>
            Log out
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}