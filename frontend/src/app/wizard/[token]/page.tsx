'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ChevronLeft, ChevronRight, Save, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/use-toast'
import { WizardBlock } from '@/components/wizard/WizardBlock'
import { AIParagraphEditor } from '@/components/wizard/AIParagraphEditor'
import { RiskBadgeInline } from '@/components/wizard/RiskBadgeInline'
import { BlockNavigation } from '@/components/wizard/BlockNavigation'
import { cn } from '@/lib/utils'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface WizardBlockDef {
  id: string
  number: number
  title: string
  description: string
  questions: Array<{
    id: string
    text: string
    type: 'text' | 'textarea' | 'select' | 'boolean' | 'multiselect'
    options?: string[]
    placeholder?: string
    why_asking?: string
    article_ref?: string
    required?: boolean
  }>
}

interface SessionState {
  session_token: string
  email: string | null
  org_name: string | null
  system_name: string | null
  current_block: string
  answers: Record<string, Record<string, string | boolean>>
  generated_paragraphs: Record<string, string>
  risk_result: string | null
  payment_confirmed: boolean
  completion_percent: number
}

export default function WizardSessionPage() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string

  const [blocks, setBlocks] = useState<WizardBlockDef[]>([])
  const [session, setSession] = useState<SessionState | null>(null)
  const [activeBlock, setActiveBlock] = useState('B1')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [riskResult, setRiskResult] = useState<{ risk_level: string; justification: string } | null>(null)

  useEffect(() => {
    Promise.all([loadBlocks(), loadSession()])
  }, [token])

  const loadBlocks = async () => {
    const res = await fetch(`${API_BASE}/api/v1/wizard/blocks`)
    const data = await res.json()
    setBlocks(data.blocks || [])
  }

  const loadSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/wizard/sessions/${token}`)
      if (!res.ok) {
        router.push('/wizard')
        return
      }
      const data = await res.json()
      setSession(data)
      setActiveBlock(data.current_block || 'B1')
      if (data.risk_result) {
        setRiskResult({ risk_level: data.risk_result, justification: '' })
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to load session.', variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveBlock = async (blockId: string, answers: Record<string, string | boolean>, advance = false) => {
    setIsSaving(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/wizard/sessions/${token}/blocks/${blockId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers, advance }),
      })
      if (!res.ok) throw new Error('Save failed')
      const updated = await res.json()
      setSession(updated)

      // Trigger risk classification after B2
      if (blockId === 'B2' || blockId === 'B1') {
        classifyRisk()
      }
    } catch {
      toast({ title: 'Save failed', description: 'Could not save answers.', variant: 'destructive' })
    } finally {
      setIsSaving(false)
    }
  }

  const classifyRisk = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/wizard/sessions/${token}/classify-risk`, {
        method: 'POST',
      })
      if (res.ok) {
        const data = await res.json()
        setRiskResult(data)
        setSession(prev => prev ? { ...prev, risk_result: data.risk_level } : prev)
      }
    } catch {}
  }

  const handleParagraphGenerated = (blockId: string, paragraph: string) => {
    setSession(prev => prev ? {
      ...prev,
      generated_paragraphs: { ...prev.generated_paragraphs, [blockId]: paragraph }
    } : prev)
  }

  const goToBlock = (blockId: string) => setActiveBlock(blockId)

  const handleCheckout = () => router.push(`/wizard/${token}/checkout`)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (!session) return null

  const activeBlockDef = blocks.find(b => b.id === activeBlock)
  const blockIndex = blocks.findIndex(b => b.id === activeBlock)
  const totalBlocks = blocks.length
  const allBlocksAnswered = blocks.every(b => {
    const ans = session.answers[b.id] || {}
    const required = b.questions.filter(q => q.required !== false)
    return required.every(q => ans[q.id] && String(ans[q.id]).trim())
  })

  const BLOCKS_SHOWING_RISK = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7']

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top bar */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-900">{session.system_name || 'Annex IV Technical File'}</p>
            <p className="text-xs text-slate-500">Technical File Completion: {session.completion_percent}%</p>
          </div>
          <div className="flex items-center gap-3">
            {isSaving && <span className="text-xs text-slate-400 flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" />Saving…</span>}
            {riskResult && <RiskBadgeInline riskLevel={riskResult.risk_level} compact />}
            {allBlocksAnswered && (
              <Button size="sm" onClick={handleCheckout}>Export PDF — €299</Button>
            )}
          </div>
        </div>
        {/* Progress bar */}
        <div className="h-1 bg-slate-100">
          <div
            className="h-1 bg-blue-600 transition-all duration-500"
            style={{ width: `${session.completion_percent}%` }}
          />
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8 flex gap-8">
        {/* Sidebar */}
        <div className="w-48 shrink-0 hidden md:block">
          <nav className="space-y-1">
            {blocks.map(b => {
              const blockAnswers = session.answers[b.id] || {}
              const required = b.questions.filter(q => q.required !== false)
              const filled = required.filter(q => blockAnswers[q.id] && String(blockAnswers[q.id]).trim()).length
              const isComplete = filled === required.length && required.length > 0
              const hasParagraph = !!session.generated_paragraphs[b.id]
              return (
                <button
                  key={b.id}
                  onClick={() => goToBlock(b.id)}
                  className={cn(
                    'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                    activeBlock === b.id
                      ? 'bg-blue-600 text-white font-semibold'
                      : 'text-slate-600 hover:bg-slate-200'
                  )}
                >
                  <span className="flex items-center justify-between">
                    <span>{b.id}: {b.title.split(' ').slice(0, 2).join(' ')}</span>
                    {isComplete && hasParagraph && <span className="text-xs">✅</span>}
                    {isComplete && !hasParagraph && <span className="text-xs">📝</span>}
                  </span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0 space-y-6">
          {/* Risk badge after B1/B2 */}
          {riskResult && BLOCKS_SHOWING_RISK.includes(activeBlock) && (
            <RiskBadgeInline riskLevel={riskResult.risk_level} justification={riskResult.justification} />
          )}

          {activeBlockDef && (
            <WizardBlock
              block={activeBlockDef}
              answers={session.answers[activeBlock] || {}}
              onSave={(answers, advance) => handleSaveBlock(activeBlock, answers, advance)}
              isSaving={isSaving}
            />
          )}

          {activeBlockDef && session.answers[activeBlock] && (
            <AIParagraphEditor
              token={token}
              blockId={activeBlock}
              existingParagraph={session.generated_paragraphs[activeBlock] || ''}
              onParagraphGenerated={(p) => handleParagraphGenerated(activeBlock, p)}
            />
          )}

          <BlockNavigation
            blocks={blocks}
            activeBlock={activeBlock}
            onNavigate={goToBlock}
            onCheckout={handleCheckout}
            completionPercent={session.completion_percent}
            allComplete={allBlocksAnswered}
          />
        </div>
      </div>
    </div>
  )
}
