import { NavLink, Outlet, useLocation } from "react-router-dom"

export function AppLayout() {
  const location = useLocation()
  const isVisionRoute = location.pathname === "/vision"

  return (
    <div className={`app-shell${isVisionRoute ? " app-shell-vision" : ""}`}>
      <header className="app-header">
        <div>
          <p className="eyebrow">EntityFlow</p>
          <h1>Extraction Review Workspace</h1>
          <p className="header-description">
            Upload documents, run extractors, and review structured entity
            results.
          </p>
        </div>

        <nav className="app-nav" aria-label="Primary navigation">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? "nav-link nav-link-active" : "nav-link"
            }
          >
            Home
          </NavLink>

          <NavLink
            to="/upload"
            className={({ isActive }) =>
              isActive ? "nav-link nav-link-active" : "nav-link"
            }
          >
            Upload
          </NavLink>

          <NavLink
            to="/vision"
            className={({ isActive }) =>
              isActive ? "nav-link nav-link-active" : "nav-link"
            }
          >
            Vision
          </NavLink>
        </nav>
      </header>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
