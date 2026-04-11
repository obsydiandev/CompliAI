'use client'

import { useState, useEffect, useRef } from 'react'
import { HelpCircle, Save, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { toast } from '@/components/ui/use-toast'
import { cn } from '@/lib/utils'

interface Question {
  id: string
  text: string
  type: 'text' | 'textarea' | 'select' | 'boolean' | 'multiselect'
  options?: string[]
  placeholder?: string
  why_asking?: string
  article_ref?: string
  required?: boolean
}

interface Block {
  id: string
  number: number
  title: string
  description: string
  questions: Question[]
}

interface WizardBlockProps {
  block: Block
  answers: Record<string, string | boolean>
  onSave: (answers: Record<string, string | boolean>, advance?: boolean) => void
  isSaving?: boolean
}

export function WizardBlock({ block, answers: initialAnswers, onSave, isSaving }: WizardBlockProps) {
  const [answers, setAnswers] = useState<Record<string, string | boolean>>(initialAnswers)
  const [showTooltip, setShowTooltip] = useState<string | null>(null)
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setAnswers(initialAnswers)
  }, [block.id])

  const handleChange = (questionId: string, value: string | boolean) => {
    const next = { ...answers, [questionId]: value }
    setAnswers(next)

    // Auto-save after 1s of inactivity
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current)
    autoSaveTimer.current = setTimeout(() => onSave(next), 1000)
  }

  const requiredQuestions = block.questions.filter(q => q.required !== false)
  const answeredRequired = requiredQuestions.filter(q => {
    const v = answers[q.id]
    return v !== undefined && v !== null && String(v).trim() !== ''
  }).length
  const isComplete = answeredRequired === requiredQuestions.length

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-blue-600 mb-1">Block {block.id}</div>
            <CardTitle className="text-xl">{block.title}</CardTitle>
            <CardDescription className="mt-1">{block.description}</CardDescription>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-slate-900">{answeredRequired}/{requiredQuestions.length}</p>
            <p className="text-xs text-slate-500">questions</p>
          </div>
        </div>
        {/* Completion bar */}
        <div className="mt-3">
          <div className="w-full bg-slate-100 rounded-full h-1.5">
            <div
              className="bg-blue-600 h-1.5 rounded-full transition-all"
              style={{ width: `${requiredQuestions.length > 0 ? (answeredRequired / requiredQuestions.length) * 100 : 0}%` }}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {block.questions.map(q => (
          <div key={q.id} className="space-y-2">
            <div className="flex items-start justify-between gap-2">
              <label className={cn('text-sm font-medium text-slate-700', !q.required && 'text-slate-500')}>
                {q.text}
                {!q.required && <span className="ml-1 text-slate-400 text-xs">(optional)</span>}
              </label>
              {q.why_asking && (
                <button
                  className="shrink-0 text-slate-400 hover:text-blue-600 transition-colors mt-0.5"
                  onClick={() => setShowTooltip(showTooltip === q.id ? null : q.id)}
                >
                  <HelpCircle className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Tooltip */}
            {showTooltip === q.id && q.why_asking && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                <p className="font-medium mb-1">Why are we asking?</p>
                <p>{q.why_asking}</p>
                {q.article_ref && (
                  <p className="mt-1 text-xs font-mono text-blue-600">{q.article_ref}</p>
                )}
              </div>
            )}

            {/* Input */}
            {q.type === 'text' && (
              <Input
                placeholder={q.placeholder}
                value={String(answers[q.id] || '')}
                onChange={e => handleChange(q.id, e.target.value)}
              />
            )}
            {q.type === 'textarea' && (
              <Textarea
                placeholder={q.placeholder}
                value={String(answers[q.id] || '')}
                onChange={e => handleChange(q.id, e.target.value)}
                rows={4}
              />
            )}
            {q.type === 'boolean' && (
              <div className="flex gap-3">
                {['Yes', 'No'].map(opt => (
                  <button
                    key={opt}
                    onClick={() => handleChange(q.id, opt === 'Yes')}
                    className={cn(
                      'px-5 py-2 border-2 rounded-lg text-sm font-medium transition-all',
                      answers[q.id] === (opt === 'Yes')
                        ? 'border-blue-600 bg-blue-50 text-blue-700'
                        : 'border-slate-200 hover:border-blue-300'
                    )}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}
            {q.type === 'select' && q.options && (
              <div className="space-y-2">
                {q.options.map(opt => (
                  <button
                    key={opt}
                    onClick={() => handleChange(q.id, opt)}
                    className={cn(
                      'w-full p-3 border-2 rounded-lg text-left text-sm transition-all',
                      answers[q.id] === opt
                        ? 'border-blue-600 bg-blue-50 text-blue-700'
                        : 'border-slate-200 hover:border-blue-300'
                    )}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        <div className="flex items-center justify-between pt-2 border-t">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {isSaving ? (
              <><Loader2 className="w-3 h-3 animate-spin" />Saving…</>
            ) : (
              <><Save className="w-3 h-3" />Auto-saved</>
            )}
          </div>
          <Button
            size="sm"
            disabled={!isComplete || isSaving}
            onClick={() => onSave(answers, false)}
          >
            Save Block
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
