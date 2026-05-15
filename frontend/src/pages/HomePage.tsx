import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"

import { getDashboardSummary } from "../api/client"
import { BackendStatus } from "../components/BackendStatus"
import type {
  DashboardFinding,
  DashboardSeverityCount,
  DashboardSummaryResponse,
  DashboardTimePoint,
} from "../types"

const emptySummary: DashboardSummaryResponse = {
  stats: {
    total_documents: 0,
    total_entities: 0,
    reviewed_entities: 0,
    extractor_count: 0,
  },
  critical_findings: [],
  recent_findings: [],
  severity_counts: [],
  findings_over_time: [],
  source_counts: [],
}

const severityOrder = ["Critical", "High", "Medium", "Low"] as const
const severityRange = {
  Critical: "90 - 100",
  High: "70 - 89",
  Medium: "40 - 69",
  Low: "1 - 39",
}

function formatNumber(value: number): string {
  return value.toLocaleString()
}

function formatSourceType(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function reviewStatusLabel(status: DashboardFinding["review_status"]): string {
  if (status === "approved" || status === "rejected") return "Reviewed"
  return "New"
}

function buildSparkPath(values: number[]): string {
  const chartValues = values.length ? values : [0, 0, 0, 0, 0, 0, 0]
  const max = Math.max(...chartValues, 1)
  const points = chartValues.map((value, index) => {
    const x = 2 + index * (52 / Math.max(chartValues.length - 1, 1))
    const y = 34 - (value / max) * 26
    return `${x.toFixed(1)} ${y.toFixed(1)}`
  })

  return `M${points.join(" L")}`
}

function buildDonutBackground(counts: DashboardSeverityCount[]): string {
  const total = counts.reduce((sum, item) => sum + item.count, 0)
  if (total === 0) {
    return "radial-gradient(circle, var(--surface) 0 43%, transparent 44%), conic-gradient(rgba(100, 116, 150, 0.22) 0 100%)"
  }

  const colors = {
    Critical: "var(--danger)",
    High: "var(--warning)",
    Medium: "#ffd730",
    Low: "var(--success)",
  }
  let cursor = 0
  const stops = severityOrder.map((severity) => {
    const count = countForSeverity(counts, severity)
    const start = cursor
    cursor += (count / total) * 100
    return `${colors[severity]} ${start}% ${cursor}%`
  })

  return `radial-gradient(circle, var(--surface) 0 43%, transparent 44%), conic-gradient(${stops.join(", ")})`
}

function buildLineChart(points: DashboardTimePoint[]) {
  const values = points.length ? points.map((point) => point.count) : [0, 0, 0, 0, 0, 0, 0]
  const max = Math.max(...values, 1)
  const coords = values.map((value, index) => ({
    x: 20 + index * (280 / Math.max(values.length - 1, 1)),
    y: 130 - (value / max) * 108,
  }))

  const line = coords.map((point, index) => `${index === 0 ? "M" : "L"}${point.x} ${point.y}`).join(" ")
  const area = `${line} L300 140 L20 140 Z`

  return { coords, line, area }
}

function countForSeverity(counts: DashboardSeverityCount[], severity: string): number {
  return counts.find((item) => item.severity === severity)?.count ?? 0
}

export function HomePage() {
  const [summary, setSummary] = useState<DashboardSummaryResponse>(emptySummary)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function loadDashboard() {
      setLoading(true)
      setError(null)

      try {
        const data = await getDashboardSummary()
        if (isMounted) setSummary(data)
      } catch (dashboardError) {
        if (!isMounted) return

        setSummary(emptySummary)
        setError(
          dashboardError instanceof Error
            ? dashboardError.message
            : "Dashboard data could not be loaded.",
        )
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadDashboard()

    return () => {
      isMounted = false
    }
  }, [])

  const stats = useMemo(
    () => [
      {
        label: "Documents",
        value: formatNumber(summary.stats.total_documents),
        change: loading ? "Loading" : "Stored records",
        tone: "blue",
        path: buildSparkPath(summary.findings_over_time.map((point) => point.count)),
      },
      {
        label: "Entities Found",
        value: formatNumber(summary.stats.total_entities),
        change: loading ? "Loading" : "Across all extractors",
        tone: "red",
        path: buildSparkPath(summary.findings_over_time.map((point) => point.count + 1)),
      },
      {
        label: "Reviewed",
        value: formatNumber(summary.stats.reviewed_entities),
        change: loading ? "Loading" : "Approved or rejected",
        tone: "purple",
        path: buildSparkPath([1, 2, 1, 3, 2, 4, summary.stats.reviewed_entities || 1]),
      },
      {
        label: "Extractors",
        value: formatNumber(summary.stats.extractor_count),
        change: loading ? "Loading" : "Active engines",
        tone: "green",
        path: buildSparkPath([1, 1, 2, 2, 3, 3, summary.stats.extractor_count || 1]),
      },
    ],
    [loading, summary],
  )

  const lineChart = buildLineChart(summary.findings_over_time)
  const severityTotal = summary.severity_counts.reduce((total, item) => total + item.count, 0)
  const feedItems = summary.recent_findings.slice(0, 5)

  return (
    <section className="dashboard-page" aria-label="EntityFlow dashboard">
      <div className="dashboard-main">
        {error && (
          <div className="dashboard-error" role="alert">
            <strong>Dashboard backend unavailable</strong>
            <span>{error}</span>
          </div>
        )}

        <div className="stat-grid">
          {stats.map((stat) => (
            <article className={`metric-card metric-${stat.tone}`} key={stat.label}>
              <div>
                <p>{stat.label}</p>
                <strong>{stat.value}</strong>
                <span>{stat.change}</span>
              </div>
              <svg className="sparkline" viewBox="0 0 56 40" aria-hidden="true">
                <path d={stat.path} />
              </svg>
            </article>
          ))}
        </div>

        <section className="dashboard-panel critical-panel">
          <header className="panel-header">
            <div>
              <h2>Latest Critical Findings</h2>
              <p>Newest high-risk extraction results requiring review.</p>
            </div>
            <Link className="panel-action" to="/upload">New Upload</Link>
          </header>

          <div className="alert-list">
            {summary.critical_findings.length === 0 ? (
              <div className="dashboard-empty">No high-risk findings yet.</div>
            ) : (
              summary.critical_findings.map((item) => (
                <article className="alert-row" key={`${item.document_id}-${item.entity_text}-${item.risk_score}`}>
                  <span className="alert-icon">!</span>
                  <div className="alert-body">
                    <div>
                      <strong>{item.document_label}</strong>
                      <span className="risk-tag">{item.entity_type}</span>
                    </div>
                    <p>Source: {item.extractor_name} · {item.entity_text}</p>
                  </div>
                  <div className="risk-score">
                    <strong>{item.risk_score}</strong>
                    <span>Risk Score</span>
                  </div>
                  <div className="alert-meta">
                    <span>{formatDateTime(item.detected_at)}</span>
                    <small>{formatSourceType(item.source_type)}</small>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="dashboard-panel">
          <header className="panel-header">
            <div>
              <h2>Recent Findings</h2>
              <p>Latest detected entities and extraction states.</p>
            </div>
            <Link className="panel-action" to="/vision">Run OCR</Link>
          </header>

          <div className="findings-table-wrap">
            <table className="findings-table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Risk Score</th>
                  <th>Detected At</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_findings.length === 0 ? (
                  <tr>
                    <td colSpan={6}>No extraction results yet.</td>
                  </tr>
                ) : (
                  summary.recent_findings.map((finding) => {
                    const status = reviewStatusLabel(finding.review_status)

                    return (
                      <tr key={`${finding.document_id}-${finding.entity_text}-${finding.detected_at}`}>
                        <td>{finding.document_label}</td>
                        <td>{finding.entity_type}</td>
                        <td>
                          <span className={`severity-pill severity-${finding.severity.toLowerCase()}`}>
                            {finding.severity}
                          </span>
                        </td>
                        <td><span className="score-pill">{finding.risk_score}</span></td>
                        <td>{formatDateTime(finding.detected_at)}</td>
                        <td className={`status-text status-${status.toLowerCase()}`}>
                          {status}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>

        <div className="chart-grid">
          <section className="dashboard-panel chart-panel">
            <h2>Findings by Severity</h2>
            <p>Distribution of entities by review priority.</p>
            <div className="donut-row">
              <div
                className="donut-chart"
                style={{ background: buildDonutBackground(summary.severity_counts) }}
                aria-label={`${severityTotal} total findings`}
              >
                <strong>{severityTotal}</strong>
                <span>Total</span>
              </div>
              <div className="legend-list">
                {severityOrder.map((severity) => {
                  const count = countForSeverity(summary.severity_counts, severity)
                  const percent = severityTotal ? Math.round((count / severityTotal) * 100) : 0

                  return (
                    <span key={severity}>
                      <i className={`dot ${severity.toLowerCase()}`} /> {severity}
                      <strong>{count} ({percent}%)</strong>
                    </span>
                  )
                })}
              </div>
            </div>
          </section>

          <section className="dashboard-panel chart-panel">
            <h2>Findings Over Time</h2>
            <p>Daily extraction trend over the last 7 days.</p>
            <svg className="line-chart" viewBox="0 0 320 160" role="img" aria-label="Findings trend line">
              <g className="chart-grid-lines">
                <path d="M20 20H300 M20 60H300 M20 100H300 M20 140H300" />
                <path d="M20 20V140 M66 20V140 M112 20V140 M158 20V140 M204 20V140 M250 20V140 M300 20V140" />
              </g>
              <path className="area-line-fill" d={lineChart.area} />
              <path className="area-line" d={lineChart.line} />
              {lineChart.coords.map((point) => (
                <circle key={`${point.x}-${point.y}`} cx={point.x} cy={point.y} r="4" />
              ))}
            </svg>
          </section>

          <section className="dashboard-panel chart-panel">
            <h2>Top Affected Documents</h2>
            <p>Documents with the highest entity risk scores.</p>
            <div className="bar-list">
              {summary.recent_findings.length === 0 ? (
                <div className="dashboard-empty">No document ranking yet.</div>
              ) : (
                summary.recent_findings.slice(0, 5).map((finding) => (
                  <div className="bar-row" key={`${finding.document_id}-${finding.entity_text}`}>
                    <span>{finding.document_label}</span>
                    <div><i style={{ width: `${Math.max(finding.risk_score, 6)}%` }} /></div>
                    <strong>{finding.risk_score}</strong>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      </div>

      <aside className="dashboard-side">
        <section className="dashboard-panel">
          <header className="side-panel-title">
            <h2>Live Monitoring Feed</h2>
            <span><i className="dot low" /> Live</span>
          </header>
          <div className="feed-list">
            {feedItems.length === 0 ? (
              <div className="dashboard-empty">No live events yet.</div>
            ) : (
              feedItems.map((item) => (
                <div className="feed-item" key={`${item.document_id}-${item.entity_text}-${item.detected_at}`}>
                  <i className={`dot ${item.severity.toLowerCase()}`} />
                  <div>
                    <strong>{item.entity_type} detected</strong>
                    <span>{item.document_label}</span>
                  </div>
                  <time>{formatDateTime(item.detected_at)}</time>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="dashboard-panel">
          <h2>Severity Legend</h2>
          <div className="severity-legend">
            {severityOrder.map((severity) => (
              <span key={severity}>
                <i className={`dot ${severity.toLowerCase()}`} /> {severity}
                <strong>{severityRange[severity]}</strong>
              </span>
            ))}
            <span><i className="dot info" /> Info <strong>Informational</strong></span>
          </div>
        </section>

        <section className="dashboard-panel">
          <header className="side-panel-title">
            <h2>Data Sources</h2>
            <Link className="panel-action" to="/upload">View All</Link>
          </header>
          <div className="source-list">
            {summary.source_counts.length === 0 ? (
              <div className="dashboard-empty">No sources yet.</div>
            ) : (
              summary.source_counts.map((source) => (
                <div className="source-row" key={source.source_type}>
                  <span>{formatSourceType(source.source_type)}</span>
                  <strong>{formatNumber(source.count)}</strong>
                </div>
              ))
            )}
          </div>
        </section>

        <BackendStatus />
      </aside>
    </section>
  )
}
