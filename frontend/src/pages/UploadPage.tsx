import { type ChangeEvent, type FormEvent, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"

import { createDocument } from "../api/client"
import { VisionPage } from "./VisionPage"

import "./UploadPage.css"

const MIN_LENGTH = 10
const MAX_LENGTH = 100_000
const ACCEPTED_EXTENSIONS = [".txt", ".md"]

type InputMode = "paste" | "file" | "image"

export function UploadPage() {
  const navigate = useNavigate()

  const [mode, setMode] = useState<InputMode>("paste")
  const [text, setText] = useState("")
  const [fileName, setFileName] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const charCount = text.length
  const isTooShort = charCount > 0 && charCount < MIN_LENGTH
  const isTooLong = charCount > MAX_LENGTH
  const isTextMode = mode === "paste" || mode === "file"
  const isValid = isTextMode && charCount >= MIN_LENGTH && charCount <= MAX_LENGTH

  /* ── helpers ─────────────────────────────────────── */

  function switchMode(next: InputMode) {
    if (loading) return
    setMode(next)
    setText("")
    setFileName(null)
    setError(null)
    setInfo(null)
  }

  function handleTextChange(e: ChangeEvent<HTMLTextAreaElement>) {
    setText(e.target.value)
    setError(null)
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    setError(null)
    setInfo(null)

    const file = e.target.files?.[0]
    if (!file) return

    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase()
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError(`Only ${ACCEPTED_EXTENSIONS.join(", ")} files are accepted.`)
      if (fileInputRef.current) fileInputRef.current.value = ""
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      const content = reader.result as string
      setText(content)
      setFileName(file.name)
    }
    reader.onerror = () => {
      setError("Could not read the file. Please try again.")
    }
    reader.readAsText(file, "utf-8")
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!isValid || loading) return

    setLoading(true)
    setError(null)
    setInfo(null)

    try {
      const sourceType = mode === "paste" ? "manual" : "file_upload"
      const response = await createDocument(text, sourceType)

      if (response.is_duplicate) {
        setInfo(
          `This document already exists (ID #${response.id}). Redirecting…`,
        )
        setTimeout(() => {
          navigate(`/documents/${response.id}`, {
            state: { isDuplicate: true },
          })
        }, 2000)
        setLoading(false)
        return
      }

      navigate(`/documents/${response.id}`)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred."
      setError(message)
      setLoading(false)
    }
  }

  /* ── char count display ──────────────────────────── */

  function charCountClass(): string {
    if (isTooLong) return "upload-char-count upload-char-error"
    if (isTooShort) return "upload-char-count upload-char-warning"
    return "upload-char-count"
  }

  function charCountLabel(): string {
    if (isTooShort) return `${charCount} / ${MIN_LENGTH} min`
    if (isTooLong) return `${charCount} / ${MAX_LENGTH} max`
    return `${charCount.toLocaleString()} characters`
  }

  /* ── render ──────────────────────────────────────── */

  return (
    <section className={`page-card upload-page-card${mode === "image" ? " upload-page-card-vision" : ""}`}>
      <div className="page-header">
        <p className="eyebrow">New document</p>
        <h2>Upload a document</h2>
        <p>
          Paste text, select a text file, or run OCR on an image from the same
          workspace.
        </p>
      </div>

      {/* ── Mode tabs ──────────────────────────────── */}
      <div className="upload-tabs" role="tablist" aria-label="Input mode">
        <button
          id="tab-paste"
          role="tab"
          type="button"
          aria-selected={mode === "paste"}
          className={`upload-tab${mode === "paste" ? " upload-tab-active" : ""}`}
          onClick={() => switchMode("paste")}
        >
          ✍️ Paste text
        </button>
        <button
          id="tab-file"
          role="tab"
          type="button"
          aria-selected={mode === "file"}
          className={`upload-tab${mode === "file" ? " upload-tab-active" : ""}`}
          onClick={() => switchMode("file")}
        >
          📄 Upload file
        </button>
        <button
          id="tab-image"
          role="tab"
          type="button"
          aria-selected={mode === "image"}
          className={`upload-tab${mode === "image" ? " upload-tab-active" : ""}`}
          onClick={() => switchMode("image")}
        >
          Image OCR
        </button>
      </div>

      {mode === "image" ? (
        <VisionPage embedded />
      ) : (
        <form onSubmit={handleSubmit}>
        {/* ── Paste mode ─────────────────────────────── */}
        {mode === "paste" && (
          <textarea
            id="upload-text-input"
            className="upload-textarea"
            placeholder="Paste your text here…"
            value={text}
            onChange={handleTextChange}
            disabled={loading}
            aria-describedby="upload-char-info"
          />
        )}

        {/* ── File mode ──────────────────────────────── */}
        {mode === "file" && (
          <div className="upload-file-zone">
            <div className="upload-file-zone-icon">📁</div>
            <p>
              Select a <strong>.txt</strong> or <strong>.md</strong> file
            </p>

            <label className="upload-file-zone-label" htmlFor="upload-file-input">
              Choose file
            </label>
            <input
              ref={fileInputRef}
              id="upload-file-input"
              className="upload-file-input"
              type="file"
              accept=".txt,.md"
              onChange={handleFileChange}
              disabled={loading}
            />

            {fileName && (
              <span className="upload-file-name">📎 {fileName}</span>
            )}
          </div>
        )}

        {/* ── Char counter ───────────────────────────── */}
        {charCount > 0 && (
          <div className="upload-meta-row" id="upload-char-info">
            <span className={charCountClass()}>{charCountLabel()}</span>
            {mode === "file" && fileName && (
              <span>
                Source: <strong>{fileName}</strong>
              </span>
            )}
          </div>
        )}

        {/* ── Actions ────────────────────────────────── */}
        <div className="upload-actions">
          <button
            id="upload-submit-button"
            type="submit"
            className="upload-submit"
            disabled={!isValid || loading}
          >
            {loading && <span className="upload-spinner" />}
            {loading ? "Uploading…" : "Upload document"}
          </button>

          {loading && (
            <span className="upload-status">
              Sending to the extraction pipeline…
            </span>
          )}
        </div>
        </form>
      )}

      {/* ── Error banner ───────────────────────────── */}
      {error && isTextMode && (
        <div className="upload-error-banner" role="alert">
          <span className="upload-error-icon">⚠️</span>
          <div>{error}</div>
        </div>
      )}

      {/* ── Info / duplicate banner ────────────────── */}
      {info && isTextMode && (
        <div className="upload-info-banner" role="status">
          <span className="upload-info-icon">ℹ️</span>
          <div>{info}</div>
        </div>
      )}
    </section>
  )
}
