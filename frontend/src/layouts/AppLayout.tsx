import { NavLink, Outlet, useLocation } from "react-router-dom"

const navItems = [
  { to: "/", label: "Dashboard", icon: "D", end: true },
  { to: "/upload", label: "Upload", icon: "U" },
  { to: "/vision", label: "Vision OCR", icon: "V" },
]

export function AppLayout() {
  const location = useLocation()
  const isVisionRoute = location.pathname === "/vision"

  return (
    <div className={`app-shell${isVisionRoute ? " app-shell-vision" : ""}`}>
      <aside className="app-sidebar" aria-label="Workspace navigation">
        <div className="app-brand">
          <span className="app-brand-mark" aria-hidden="true">E</span>
          <div>
            <p className="eyebrow">EntityFlow</p>
            <h1>AI Entity Detection System</h1>
          </div>
        </div>

        <nav className="app-nav" aria-label="Primary navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                isActive ? "nav-link nav-link-active" : "nav-link"
              }
            >
              <span className="nav-link-icon" aria-hidden="true">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-status">
          <span className="status-dot status-dot-live" />
          <div>
            <strong>Live Monitoring</strong>
            <span>All systems operational</span>
          </div>
        </div>
      </aside>

      <div className="app-workspace">
        <header className="app-header">
          <label className="app-search">
            <span aria-hidden="true">Search</span>
            <input
              type="search"
              placeholder="Search documents, entities, extractors..."
            />
          </label>

          <div className="app-header-actions">
            <button className="icon-button" type="button" aria-label="Notifications">
              <span className="notification-dot">2</span>
              N
            </button>
            <button className="icon-button" type="button" aria-label="Theme">
              M
            </button>
            <div className="user-chip" aria-label="Current user">
              <span>A</span>
              <div>
                <strong>Admin</strong>
                <small>Workspace</small>
              </div>
            </div>
          </div>
        </header>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
