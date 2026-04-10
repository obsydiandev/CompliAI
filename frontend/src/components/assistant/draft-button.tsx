'use client'

import { useState, useRef } from 'react'
import { Sparkles, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/use-toast'

const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1'

interface DraftButtonProps {
  systemId: string
  sectionNumber: number
  /** Called when a draft is applied to the form. Receives field→value map. */
  onApplyDraft: (draft: Record<string, unknown>) => void
}

/**
 * AI draft generation button with streaming SSE support.
 * Uses EventSource (SSE) to stream the draft token by token,
 * then offers the user a preview before applying it.
 */
export function DraftButton({ systemId, sectionNumber, onApplyDraft }: DraftButtonProps) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamedText, setStreamedText] = useState('')
  const [parsedDraft, setParsedDraft] = useState<Record<string, unknown> | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const abortRef = useRef<(() => void) | null>(null)

  function getToken() {
    if (typeof window !== 'undefined') return localStorage.getItem('compliai_token')
    return null
  }

  async function handleGenerate() {
    if (isStreaming) {
      abortRef.current?.()
      return
    }

    setIsStreaming(true)
    setStreamedText('')
    setParsedDraft(null)
    setShowPreview(false)

    const token = getToken()
    const url = `${BASE_URL}/systems/${systemId}/assistant/stream/${sectionNumber}`

    try {
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(err.detail || `HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''
      let cancelled = false

      abortRef.current = () => {
        cancelled = true
        reader?.cancel()
        setIsStreaming(false)
      }

      while (reader) {
        const { done, value } = await reader.read()
        if (done || cancelled) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') break
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) {
              toast({ variant: 'destructive', title: 'Draft generation failed', description: parsed.error })
              setIsStreaming(false)
              return
            }
            if (parsed.delta) {
              accumulated += parsed.delta
              setStreamedText(accumulated)
            }
          } catch {
            // Ignore malformed lines
          }
        }
      }

      // Try to parse final accumulated JSON
      if (accumulated.trim()) {
        try {
          const jsonMatch = accumulated.match(/\{[\s\S]*\}/)
          if (jsonMatch) {
            const draft = JSON.parse(jsonMatch[0]) as Record<string, unknown>
            setParsedDraft(draft)
            setShowPreview(true)
          }
        } catch {
          // If not valid JSON, still show the streamed text as preview
          setShowPreview(true)
        }
      }
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Draft generation failed',
        description: err instanceof Error ? err.message : 'Unexpected error',
      })
    } finally {
      setIsStreaming(false)
    }
  }

  function handleApply() {
    if (parsedDraft) {
      onApplyDraft(parsedDraft)
      toast({ title: 'Draft applied', description: 'Review and save the generated content.' })
      setShowPreview(false)
      setParsedDraft(null)
      setStreamedText('')
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleGenerate}
          disabled={false}
          className="gap-1.5 border-primary/40 text-primary hover:bg-primary/5"
        >
          {isStreaming ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <Sparkles className="h-3.5 w-3.5" />
              AI Draft
            </>
          )}
        </Button>
        {parsedDraft && (
          <Badge variant="outline" className="text-xs text-green-600 border-green-400">
            Draft ready
          </Badge>
        )}
        {(streamedText || parsedDraft) && (
          <button
            type="button"
            onClick={() => setShowPreview((v) => !v)}
            className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-0.5"
          >
            {showPreview ? (
              <>
                <ChevronUp className="h-3 w-3" />Hide
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3" />Preview
              </>
            )}
          </button>
        )}
      </div>

      {showPreview && (
        <div className="rounded-md border bg-muted/40 p-3 space-y-3">
          <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
            AI-Generated Draft Preview
          </div>
          <pre className="text-xs whitespace-pre-wrap max-h-48 overflow-y-auto text-foreground">
            {isStreaming ? streamedText : (streamedText || JSON.stringify(parsedDraft, null, 2))}
            {isStreaming && <span className="animate-pulse">▌</span>}
          </pre>
          {parsedDraft && !isStreaming && (
            <div className="flex gap-2">
              <Button size="sm" onClick={handleApply} className="h-7 text-xs">
                Apply to form
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs"
                onClick={() => {
                  setShowPreview(false)
                  setParsedDraft(null)
                  setStreamedText('')
                }}
              >
                Discard
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
