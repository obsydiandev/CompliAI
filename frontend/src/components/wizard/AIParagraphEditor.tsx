'use client'

import { useState, useRef } from 'react'
import { Wand2, RefreshCw, Edit3, Check, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/components/ui/use-toast'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AIParagraphEditorProps {
  token: string
  blockId: string
  existingParagraph: string
  onParagraphGenerated: (paragraph: string) => void
}

export function AIParagraphEditor({
  token,
  blockId,
  existingParagraph,
  onParagraphGenerated,
}: AIParagraphEditorProps) {
  const [paragraph, setParagraph] = useState(existingParagraph)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [streamedText, setStreamedText] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  const generate = async () => {
    setIsGenerating(true)
    setStreamedText('')
    abortRef.current = new AbortController()

    try {
      const res = await fetch(`${API_BASE}/api/v1/wizard/sessions/${token}/generate-paragraph/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ block_id: blockId }),
        signal: abortRef.current.signal,
      })

      if (!res.ok) throw new Error('Generation failed')

      const reader = res.body?.getReader()
      if (!reader) throw new Error('No stream')

      const decoder = new TextDecoder()
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (data === '[DONE]') {
              setParagraph(accumulated)
              onParagraphGenerated(accumulated)
              setStreamedText('')
              break
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.delta) {
                accumulated += parsed.delta
                setStreamedText(accumulated)
              }
              if (parsed.error) throw new Error(parsed.error)
            } catch {}
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        toast({ title: 'Generation failed', description: 'Could not generate paragraph.', variant: 'destructive' })
      }
    } finally {
      setIsGenerating(false)
    }
  }

  const displayText = isGenerating ? streamedText : paragraph

  return (
    <Card className="border-blue-100">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Wand2 className="w-4 h-4 text-blue-600" />
            AI-Generated Annex IV Paragraph
          </CardTitle>
          <div className="flex items-center gap-2">
            {paragraph && !isGenerating && (
              <Button
                variant="ghost"
                size="sm"
                className="gap-1 text-xs"
                onClick={() => setIsEditing(!isEditing)}
              >
                {isEditing ? <><Check className="w-3 h-3" />Done</> : <><Edit3 className="w-3 h-3" />Edit</>}
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              className="gap-1 text-xs"
              disabled={isGenerating}
              onClick={generate}
            >
              {isGenerating ? (
                <><Loader2 className="w-3 h-3 animate-spin" />Generating…</>
              ) : paragraph ? (
                <><RefreshCw className="w-3 h-3" />Regenerate</>
              ) : (
                <><Wand2 className="w-3 h-3" />Generate Paragraph</>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {!displayText && !isGenerating && (
          <div className="text-center py-8 text-slate-400">
            <Wand2 className="w-8 h-8 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Click "Generate Paragraph" to create a formal Annex IV paragraph from your answers.</p>
          </div>
        )}
        {displayText && (
          isEditing ? (
            <Textarea
              value={paragraph}
              onChange={e => setParagraph(e.target.value)}
              onBlur={() => onParagraphGenerated(paragraph)}
              rows={8}
              className="font-mono text-sm"
            />
          ) : (
            <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
              {displayText}
              {isGenerating && <span className="animate-pulse">▊</span>}
            </div>
          )
        )}
        {paragraph && (
          <p className="text-xs text-slate-400 mt-3">
            This paragraph is AI-generated from your answers. Review and edit as needed before export.
          </p>
        )}
      </CardContent>
    </Card>
  )
}
