'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Head from 'next/head'
import { Shield, AlertTriangle, CheckCircle, ChevronRight, ChevronLeft, Share2, Mail } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/use-toast'
import { PanicCalendar } from '@/components/classifier/PanicCalendar'
import { cn } from '@/lib/utils'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Question {
  id: string
  text: string
  type: 'select' | 'boolean' | 'text'
  options?: string[]
  article_ref: string
}

interface ClassifyResult {
  lead_id: string
  share_token: string
  risk_level: 'high_risk' | 'limited_risk' | 'minimal_risk'
  justification: string
  article_citations: string[]
  annex_iii_category: string | null
  panic_calendar: Array<{
    date: string
    label: string
    description: string
    article_ref: string
    days_remaining: number
    urgency: 'past' | 'green' | 'orange' | 'red'
  }>
  primary_deadline: {
    date: string
    label: string
    days_remaining: number
    urgency: string
  }
}

const RISK_CONFIG = {
  high_risk: {
    label: 'High Risk',
    color: 'bg-red-100 text-red-800 border-red-300',
    icon: AlertTriangle,
    iconColor: 'text-red-600',
    headline: 'Your AI system is classified as High-Risk under EU AI Act Annex III.',
    cta: 'You need an Annex IV Technical File by August 2, 2026.',
  },
  limited_risk: {
    label: 'Limited Risk',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    icon: Shield,
    iconColor: 'text-yellow-600',
    headline: 'Your AI system has transparency obligations under Art. 52.',
    cta: 'Disclosure notices are required — no full Technical File needed.',
  },
  minimal_risk: {
    label: 'Minimal Risk',
    color: 'bg-green-100 text-green-800 border-green-300',
    icon: CheckCircle,
    iconColor: 'text-green-600',
    headline: 'Your AI system falls under the minimal-risk category.',
    cta: 'No mandatory documentation required. Voluntary codes of conduct apply.',
  },
}

export default function ClassifierPage() {
  const router = useRouter()
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentStep, setCurrentStep] = useState(0) // 0 = loading questions
  const [answers, setAnswers] = useState<Record<string, string | boolean>>({})
  const [result, setResult] = useState<ClassifyResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [emailSent, setEmailSent] = useState(false)
  const [started, setStarted] = useState(false)

  const loadQuestions = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/classifier/questions`)
      const data = await res.json()
      setQuestions(data.questions || [])
      setCurrentStep(1)
      setStarted(true)
    } catch {
      toast({ title: 'Error', description: 'Failed to load questions. Please try again.', variant: 'destructive' })
    }
  }

  const handleAnswer = (questionId: string, value: string | boolean) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }))
  }

  const handleSubmit = async () => {
    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/classifier/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers, use_llm_fallback: true }),
      })
      if (!res.ok) throw new Error('Classification failed')
      const data = await res.json()
      setResult(data)
      setCurrentStep(questions.length + 1)
    } catch {
      toast({ title: 'Error', description: 'Classification failed. Please try again.', variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleEmailCapture = async () => {
    if (!result || !email) return
    try {
      await fetch(`${API_BASE}/api/v1/classifier/capture-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_id: result.lead_id, email }),
      })
      setEmailSent(true)
      toast({ title: 'Got it!', description: "We'll send you a PDF summary and next steps." })
    } catch {
      toast({ title: 'Error', description: 'Failed to save email.', variant: 'destructive' })
    }
  }

  const handleShare = () => {
    if (!result) return
    const url = `${window.location.origin}/classifier/result/${result.share_token}`
    navigator.clipboard.writeText(url)
    toast({ title: 'Link copied!', description: 'Share this link on LinkedIn or with your team.' })
  }

  const currentQuestion = questions[currentStep - 1]
  const progress = started ? Math.round((currentStep / (questions.length + 1)) * 100) : 0

  return (
    <>
      <head>
        <title>AI Act Risk Classifier — Is your AI system High-Risk? | CompliAI</title>
        <meta
          name="description"
          content="Free AI Act Annex III risk checker. Answer 10 questions to find out if your AI system requires an Annex IV Technical File under the EU AI Act. No registration required."
        />
        <meta name="keywords" content="AI Act Annex IV generator, AI Act High Risk checker, Annex IV template download, EU AI Act compliance" />
        <meta property="og:title" content="Is your AI system High-Risk under the EU AI Act?" />
        <meta property="og:description" content="Free 10-question classifier. Instant result. No registration required." />
      </head>

      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        {/* Hero */}
        {!started && (
          <div className="max-w-3xl mx-auto px-4 py-16 text-center">
            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full mb-6">
              <Shield className="w-4 h-4" />
              Free — no registration required
            </div>
            <h1 className="text-4xl font-bold text-slate-900 mb-4">
              Is your AI system High-Risk under the EU AI Act?
            </h1>
            <p className="text-lg text-slate-600 mb-8">
              Answer 10 questions to get an instant Annex III risk classification with
              article citations, AI Act deadline calendar, and next steps.
            </p>
            <Button size="lg" className="gap-2" onClick={loadQuestions}>
              Start Free Classifier <ChevronRight className="w-4 h-4" />
            </Button>
            <p className="text-sm text-slate-500 mt-4">
              The AI Act High-Risk deadline for Annex III systems is <strong>August 2, 2026</strong>.
            </p>
          </div>
        )}

        {/* Questions */}
        {started && currentStep <= questions.length && currentQuestion && (
          <div className="max-w-2xl mx-auto px-4 py-12">
            {/* Progress */}
            <div className="mb-8">
              <div className="flex justify-between text-sm text-slate-500 mb-2">
                <span>Question {currentStep} of {questions.length}</span>
                <span>{progress}% complete</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <Card>
              <CardHeader>
                <div className="text-xs text-blue-600 font-mono mb-1">{currentQuestion.article_ref}</div>
                <CardTitle className="text-xl">{currentQuestion.text}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {currentQuestion.type === 'boolean' && (
                  <div className="grid grid-cols-2 gap-3">
                    {['Yes', 'No'].map(opt => (
                      <button
                        key={opt}
                        onClick={() => {
                          handleAnswer(currentQuestion.id, opt === 'Yes')
                          if (currentStep < questions.length) setCurrentStep(s => s + 1)
                          else handleSubmit()
                        }}
                        className={cn(
                          'p-4 border-2 rounded-lg text-center font-medium transition-all',
                          answers[currentQuestion.id] === (opt === 'Yes')
                            ? 'border-blue-600 bg-blue-50 text-blue-700'
                            : 'border-slate-200 hover:border-blue-300'
                        )}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                )}
                {currentQuestion.type === 'select' && currentQuestion.options && (
                  <div className="space-y-2">
                    {currentQuestion.options.map(opt => (
                      <button
                        key={opt}
                        onClick={() => {
                          handleAnswer(currentQuestion.id, opt)
                          if (currentStep < questions.length) setCurrentStep(s => s + 1)
                          else handleSubmit()
                        }}
                        className={cn(
                          'w-full p-3 border-2 rounded-lg text-left text-sm transition-all',
                          answers[currentQuestion.id] === opt
                            ? 'border-blue-600 bg-blue-50 text-blue-700'
                            : 'border-slate-200 hover:border-blue-300'
                        )}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                )}
                {currentQuestion.type === 'text' && (
                  <div className="space-y-3">
                    <textarea
                      className="w-full border border-slate-300 rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={4}
                      placeholder="Describe your AI system..."
                      value={String(answers[currentQuestion.id] || '')}
                      onChange={e => handleAnswer(currentQuestion.id, e.target.value)}
                    />
                    <Button
                      className="w-full"
                      disabled={!answers[currentQuestion.id] || isLoading}
                      onClick={() => {
                        if (currentStep < questions.length) setCurrentStep(s => s + 1)
                        else handleSubmit()
                      }}
                    >
                      {currentStep < questions.length ? 'Next' : isLoading ? 'Classifying…' : 'Get Result'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {currentStep > 1 && (
              <button
                className="mt-4 text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1"
                onClick={() => setCurrentStep(s => s - 1)}
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </button>
            )}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="max-w-3xl mx-auto px-4 py-12 space-y-6">
            {/* Risk badge */}
            {(() => {
              const cfg = RISK_CONFIG[result.risk_level]
              const Icon = cfg.icon
              return (
                <Card className={cn('border-2', cfg.color.replace('bg-', 'border-').replace('text-', '').replace(/-\d+/g, '-300'))}>
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <Icon className={cn('w-8 h-8 mt-1 flex-shrink-0', cfg.iconColor)} />
                      <div>
                        <Badge className={cn('mb-2', cfg.color)}>{cfg.label}</Badge>
                        <p className="font-semibold text-lg">{cfg.headline}</p>
                        <p className="text-sm text-slate-600 mt-1">{cfg.cta}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })()}

            {/* Justification */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Classification Justification</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-700 leading-relaxed">{result.justification}</p>
                {result.article_citations.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {result.article_citations.map(c => (
                      <span key={c} className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-1 rounded">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Panic Calendar */}
            <PanicCalendar milestones={result.panic_calendar} />

            {/* Email capture */}
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="pt-6">
                {!emailSent ? (
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Input
                      type="email"
                      placeholder="your@email.com"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      className="bg-white"
                    />
                    <Button onClick={handleEmailCapture} disabled={!email} className="gap-2 shrink-0">
                      <Mail className="w-4 h-4" /> Get PDF Summary
                    </Button>
                  </div>
                ) : (
                  <p className="text-sm text-blue-800 font-medium">
                    ✅ Check your inbox for a PDF summary and next steps.
                  </p>
                )}
                <p className="text-xs text-slate-500 mt-2">Optional — receive a PDF summary and AI Act deadline reminders.</p>
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Button size="lg" className="flex-1" onClick={() => router.push('/wizard')}>
                Generate Annex IV Technical File — €299
              </Button>
              <Button variant="outline" size="lg" className="gap-2" onClick={handleShare}>
                <Share2 className="w-4 h-4" /> Share Result
              </Button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
