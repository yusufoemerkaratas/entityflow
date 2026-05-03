import { useEffect, useState } from "react"

import { getHealth } from "../api/client"
import type { HealthResponse } from "../types"

type BackendStatusState =
  | {
      kind: "loading"
    }
  | {
      kind: "online"
      data: HealthResponse
    }
  | {
      kind: "offline"
      message: string
    }

export function BackendStatus() {
  const [state, setState] = useState<BackendStatusState>({
    kind: "loading",
  })

  useEffect(() => {
    let isMounted = true

    async function checkBackend() {
      try {
        const data = await getHealth()

        if (isMounted) {
          setState({
            kind: "online",
            data,
          })
        }
      } catch (error) {
        if (isMounted) {
          setState({
            kind: "offline",
            message:
              error instanceof Error
                ? error.message
                : "Unknown backend connection error",
          })
        }
      }
    }

    checkBackend()

    return () => {
      isMounted = false
    }
  }, [])

  if (state.kind === "loading") {
    return (
      <section className="status-card">
        <div className="status-indicator status-loading" />
        <div>
          <h3>Checking backend connection...</h3>
          <p>Trying to reach the FastAPI health endpoint.</p>
        </div>
      </section>
    )
  }

  if (state.kind === "offline") {
    return (
      <section className="status-card status-card-error">
        <div className="status-indicator status-offline" />
        <div>
          <h3>Backend unavailable</h3>
          <p>{state.message}</p>
        </div>
      </section>
    )
  }

  return (
    <section className="status-card status-card-success">
      <div className="status-indicator status-online" />
      <div>
        <h3>Backend online</h3>
        <p>
          API status: <strong>{state.data.status}</strong> · Database:{" "}
          <strong>{state.data.db}</strong>
        </p>
      </div>
    </section>
  )
}