import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import type { RegulationOption } from '../types'
import { fetchRegulations, triggerCascade } from '../api'

const JURISDICTION_COLORS: Record<string, string> = {
  EU: 'var(--color-accent)',
  US: 'var(--color-priority-high)',
  APAC: 'var(--color-priority-medium)',
}

export default function TriggerPage() {
  const navigate = useNavigate()
  const [regulations, setRegulations] = useState<RegulationOption[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [customText, setCustomText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingList, setLoadingList] = useState(true)

  useEffect(() => {
    fetchRegulations()
      .then((data) => {
        setRegulations(data)
        setLoadingList(false)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load regulations')
        setLoadingList(false)
      })
  }, [])

  const selectedReg = regulations.find((r) => r.regulation_id === selectedId)

  const handleTrigger = useCallback(async () => {
    const text = customText.trim() || selectedReg?.summary || ''
    if (!text) {
      setError('Select a regulation or enter custom text')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await triggerCascade({
        regulation_text: text,
        regulation_title: selectedReg?.title || 'Custom Regulation',
      })
      navigate(`/pipeline/${response.room_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger cascade')
      setLoading(false)
    }
  }, [customText, selectedReg, navigate])

  return (
    <div className="mx-auto min-h-screen max-w-3xl">
      {/* Header */}
      <header className="animate-header-reveal border-b border-[var(--color-surface-2)] px-6 py-8 sm:px-8">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl"
            style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-muted)' }}
          >
            <svg className="h-5 w-5 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[var(--color-ink)]" style={{ letterSpacing: '-0.02em' }}>
              RegIQ
            </h1>
            <p className="text-sm text-[var(--color-ink-dim)]">Regulatory Compliance Intelligence</p>
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="px-6 py-6 sm:px-8">
        <section className="animate-fade-in-up">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-ink-dim)]">
            Trigger Compliance Analysis
          </h2>
          <p className="mt-1.5 text-sm leading-relaxed text-[var(--color-ink-muted)]" style={{ maxWidth: '65ch' }}>
            Select a regulation to analyze. RegIQ's 5-agent cascade will parse requirements, map them to your
            company processes, identify compliance gaps, and generate a remediation plan for human review.
          </p>
        </section>

        {/* Regulation picker */}
        <section className="mt-6 animate-fade-in-up" style={{ animationDelay: '60ms' }}>
          {loadingList ? (
            <div className="flex flex-col gap-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="animate-pulse rounded-lg border border-[var(--color-surface-2)] px-4 py-4"
                  style={{ background: 'var(--color-surface-1)' }}
                >
                  <div className="h-5 w-3/4 rounded bg-[var(--color-surface-2)]" />
                  <div className="mt-2 h-4 w-full rounded bg-[var(--color-surface-2)]" />
                </div>
              ))}
            </div>
          ) : regulations.length === 0 ? (
            <div
              className="rounded-lg border border-[var(--color-surface-2)] px-4 py-6 text-center"
              style={{ background: 'var(--color-surface-1)' }}
            >
              <p className="text-sm text-[var(--color-ink-muted)]">No regulations available</p>
              <p className="mt-1 text-xs text-[var(--color-ink-dim)]">
                Add JSON files to data/mock_regulations/ to populate this list
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-2.5" role="radiogroup" aria-label="Select a regulation">
              {regulations.map((reg, i) => {
                const isSelected = selectedId === reg.regulation_id
                const accentColor = JURISDICTION_COLORS[reg.jurisdiction] || 'var(--color-accent)'
                return (
                  <button
                    key={reg.regulation_id}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    onClick={() => {
                      setSelectedId(reg.regulation_id)
                      setCustomText('')
                      setError(null)
                    }}
                    className="animate-stagger rounded-lg border px-4 py-3.5 text-left transition-all duration-150 active:scale-[0.99]"
                    style={{
                      animationDelay: `${i * 50}ms`,
                      '--i': i,
                      background: isSelected ? 'var(--color-accent-bg)' : 'var(--color-surface-1)',
                      borderColor: isSelected ? 'var(--color-accent)' : 'var(--color-surface-2)',
                      cursor: 'pointer',
                    } as React.CSSProperties}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span
                            className="rounded px-1.5 py-0.5 text-[10px] font-semibold tracking-wide"
                            style={{ background: `${accentColor}20`, color: accentColor }}
                          >
                            {reg.jurisdiction}
                          </span>
                          <span className="text-xs font-medium text-[var(--color-ink-dim)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
                            {reg.regulation_id}
                          </span>
                        </div>
                        <h3 className="mt-1.5 text-sm font-semibold text-[var(--color-ink)]">{reg.title}</h3>
                        <p className="mt-1 text-xs leading-relaxed text-[var(--color-ink-muted)]" style={{ maxWidth: '60ch' }}>
                          {reg.summary}
                        </p>
                      </div>
                      <div className="shrink-0">
                        <div
                          className="flex h-5 w-5 items-center justify-center rounded-full border-2 transition-all duration-150"
                          style={{
                            borderColor: isSelected ? 'var(--color-accent)' : 'var(--color-surface-3)',
                            background: isSelected ? 'var(--color-accent)' : 'transparent',
                          }}
                        >
                          {isSelected && (
                            <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </section>

        {/* Custom text input (collapsible) */}
        <section className="mt-5 animate-fade-in-up" style={{ animationDelay: '120ms' }}>
          <details className="rounded-lg border border-[var(--color-surface-2)]" style={{ background: 'var(--color-surface-1)' }}>
            <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-[var(--color-ink-muted)] transition-colors duration-150 hover:text-[var(--color-ink)]">
              Or paste custom regulation text
            </summary>
            <div className="border-t border-[var(--color-surface-2)] px-4 py-3">
              <textarea
                value={customText}
                onChange={(e) => {
                  setCustomText(e.target.value)
                  if (e.target.value) setSelectedId(null)
                }}
                placeholder="Paste the full text of a regulation here..."
                rows={6}
                className="w-full resize-y rounded-lg border border-[var(--color-surface-2)] bg-[var(--color-surface-0)] px-3 py-2.5 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-dim)] focus:border-[var(--color-accent)] focus:outline-none transition-colors duration-150"
                style={{ fontFamily: 'var(--font-mono)' }}
              />
              <p className="mt-1.5 text-xs text-[var(--color-ink-dim)]">
                The Monitor agent accepts raw legislative text and extracts the key requirements automatically.
              </p>
            </div>
          </details>
        </section>

        {/* Error */}
        {error && (
          <div
            className="animate-fade-in-up mt-4 rounded-lg border border-[var(--color-priority-critical)] bg-[var(--color-priority-critical-bg)] px-4 py-3 text-sm text-[var(--color-priority-critical)]"
            role="alert"
          >
            {error}
          </div>
        )}

        {/* Submit button */}
        <div className="mt-6 pb-8">
          <button
            type="button"
            onClick={handleTrigger}
            disabled={loading || (!selectedId && !customText.trim())}
            className="w-full rounded-lg bg-[var(--color-accent)] px-4 py-3.5 text-sm font-semibold text-white shadow-[0_0_20px_var(--color-accent-glow)] transition-all duration-150 hover:shadow-[0_0_30px_var(--color-accent-glow)] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
          >
            <span className="flex items-center justify-center gap-2">
              {loading ? (
                <>
                  <svg className="animate-spinner h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Triggering cascade...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Start Compliance Analysis
                </>
              )}
            </span>
          </button>
          <p className="mt-2 text-center text-xs text-[var(--color-ink-dim)]">
            5 agents will process your regulation in sequence (~75 seconds)
          </p>
        </div>
      </div>
    </div>
  )
}
