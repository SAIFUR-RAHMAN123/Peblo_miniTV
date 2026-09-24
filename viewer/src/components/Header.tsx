import { Link, NavLink } from "react-router-dom";

export function Header() {
  return (
    <header className="viewer-header">
      <Link to="/" className="viewer-logo">
        Peblo miniTV
      </Link>

      <nav>
        <NavLink to="/" className={({ isActive }) => isActive ? "active" : ""}>
          Home
        </NavLink>

        <NavLink to="/search" className={({ isActive }) => isActive ? "active" : ""}>
          Search
        </NavLink>
      </nav>
    </header>
  );
}