'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ShieldCheck, ArrowRight, Check, Sparkles, FileText, GitBranch, Bell } from 'lucide-react'
import { systemApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/use-toast'
import { cn } from '@/lib/utils'

const STEPS = [
  { id: 1, title: 'Welcome', description: 'Get started with CompliAI' },
  { id: 2, title: 'AI System', description: 'Describe your AI system' },
  { id: 3, title: 'Risk Profile', description: 'Classify risk and applicability' },
  { id: 4, title: 'Sample Data', description: 'Jumpstart with template data' },
  { id: 5, title: "You're set!", description: 'Start your compliance journey' },
]

const SAMPLE_DATA_OPTIONS = [
  {
    id: 'credit',
    name: 'Credit Risk Scorer',
    icon: '💳',
    desc: 'Pre-filled for a high-risk credit scoring model — common in fintech',
  },
  {
    id: 'cv',
    name: 'CV Ranking System',
    icon: '📄',
    desc: 'Pre-filled for AI-assisted recruitment — HR/talent use case',
  },
  {
    id: 'medical',
    name: 'Medical Diagnostic AI',
    icon: '🏥',
    desc: 'Pre-filled for medical device AI under MDR / high-risk Annex III',
  },
  {
    id: 'none',
    name: 'Start from scratch',
    icon: '✏️',
    desc: 'Empty Technical File — fill in all sections manually',
  },
]

const systemSchema = z.object({
  name: z.string().min(2, 'System name must be at least 2 characters'),
  description: z.string().optional(),
  intended_purpose: z.string().min(10, 'Please describe the intended purpose (min 10 characters)'),
})

const riskSchema = z.object({
  category: z.enum(['high_risk', 'limited_risk', 'minimal_risk']),
  annex_iii: z.boolean(),
})

type SystemForm = z.infer<typeof systemSchema>
type RiskForm = z.infer<typeof riskSchema>

export default function OnboardingPage() {
  const router = useRouter()
  const currentOrg = useAuthStore((s) => s.currentOrg)
  const [step, setStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [createdSystemId, setCreatedSystemId] = useState<string | null>(null)
  const [selectedSample, setSelectedSample] = useState<string>('none')

  const systemForm = useForm<SystemForm>({
    resolver: zodResolver(systemSchema),
  })

  const riskForm = useForm<RiskForm>({
    resolver: zodResolver(riskSchema),
    defaultValues: { category: 'high_risk', annex_iii: false },
  })

  async function onSubmitSystem(data: SystemForm) {
    if (!currentOrg) {
      toast({ variant: 'destructive', title: 'No organisation found' })
      return
    }
    setIsLoading(true)
    try {
      const riskData = riskForm.getValues()
      const res = await systemApi.create({
        org_id: currentOrg.id,
        name: data.name,
        description: data.description,
        intended_purpose: data.intended_purpose,
        category: riskData.category,
        annex_iii_classification: riskData.annex_iii,
      })
      setCreatedSystemId(res.data.id)
    } catch {
      toast({ variant: 'destructive', title: 'Failed to create AI system' })
      setIsLoading(false)
      return
    }
    setIsLoading(false)
    setStep(4)
  }

  async function onApplySample() {
    setIsLoading(true)
    try {
      // Apply template if not "none"
      if (selectedSample !== 'none' && createdSystemId) {
        const { templateApi } = await import('@/lib/api')
        // Get templates list to find matching template
        const tmplRes = await templateApi.list()
        const templates = tmplRes.data as { id: string; name: string }[]
        const sampleMap: Record<string, string> = {
          credit: 'Credit Scoring System',
          cv: 'CV Ranking / Recruitment System',
          medical: 'Medical Diagnostic AI',
        }
        const matchingName = sampleMap[selectedSample]
        const tpl = templates.find((t) => t.name === matchingName)
        if (tpl) {
          // Get the technical file revision ID first
          const { default: api } = await import('@/lib/api')
          const tfRes = await api.get(`/systems/${createdSystemId}/technical-file`)
          const revisionId = tfRes.data?.current_revision_id
          if (revisionId) {
            await templateApi.apply(createdSystemId, tpl.id, revisionId, false)
          }
        }
      }
      setStep(5)
    } catch {
      // Non-critical — still proceed to step 5
      setStep(5)
    } finally {
      setIsLoading(false)
    }
  }

  function goToDashboard() {
    router.push('/dashboard')
  }

  function goToSystem() {
    if (createdSystemId) {
      router.push(`/systems/${createdSystemId}`)
    } else {
      router.push('/dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="flex flex-col items-center space-y-3 text-center">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold">CompliAI</span>
          </div>
          <p className="text-muted-foreground">EU AI Act Compliance Platform</p>
        </div>

        {/* Step progress */}
        <div className="flex items-center justify-center gap-1.5">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-1.5">
              <div
                className={cn(
                  'flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium border-2 transition-colors',
                  step > s.id
                    ? 'bg-primary border-primary text-primary-foreground'
                    : step === s.id
                    ? 'border-primary text-primary'
                    : 'border-muted-foreground/30 text-muted-foreground'
                )}
              >
                {step > s.id ? <Check className="h-4 w-4" /> : s.id}
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={cn(
                    'h-0.5 w-8 transition-colors',
                    step > s.id ? 'bg-primary' : 'bg-muted-foreground/20'
                  )}
                />
              )}
            </div>
          ))}
        </div>
        <p className="text-center text-sm text-muted-foreground -mt-4">
          Step {step} of {STEPS.length} — {STEPS[step - 1]?.description}
        </p>

        {/* ── Step 1: Welcome ─────────────────────────────────────────────────── */}
        {step === 1 && (
          <Card>
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Welcome to CompliAI 👋</CardTitle>
              <CardDescription className="text-base">
                Your 14-day free trial has started. Let&apos;s get your EU AI Act compliance set up
                in minutes.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                {[
                  {
                    icon: FileText,
                    title: 'Annex IV Technical File',
                    desc: 'Auto-generate all 9 sections required by Art. 11',
                  },
                  {
                    icon: Sparkles,
                    title: 'AI Copilot',
                    desc: 'Drafts, suggestions & Q&A powered by GPT-4o',
                  },
                  {
                    icon: GitBranch,
                    title: 'MLOps Integrations',
                    desc: 'Link GitHub, GitLab, MLflow, W&B deployments',
                  },
                  {
                    icon: Bell,
                    title: 'Continuous Compliance',
                    desc: 'Automated policy checks & alerts for your portfolio',
                  },
                ].map((item) => (
                  <div
                    key={item.title}
                    className="flex items-start gap-3 p-4 rounded-lg border bg-muted/30"
                  >
                    <item.icon className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-sm">{item.title}</p>
                      <p className="text-xs text-muted-foreground">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
              <Button className="w-full" size="lg" onClick={() => setStep(2)}>
                Get started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <p className="text-center text-xs text-muted-foreground">
                Skip for now and{' '}
                <button
                  type="button"
                  onClick={goToDashboard}
                  className="underline hover:text-foreground"
                >
                  go to dashboard
                </button>
              </p>
            </CardContent>
          </Card>
        )}

        {/* ── Step 2: AI System name + purpose ──────────────────────────────── */}
        {step === 2 && (
          <Card>
            <CardHeader>
              <CardTitle>Tell us about your AI system</CardTitle>
              <CardDescription>
                This will be the core identity of your Annex IV Technical File.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium">System name *</label>
                  <Input
                    placeholder="e.g. Credit Risk Scorer v2"
                    {...systemForm.register('name')}
                  />
                  {systemForm.formState.errors.name && (
                    <p className="text-xs text-destructive">
                      {systemForm.formState.errors.name.message}
                    </p>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Intended purpose *</label>
                  <Textarea
                    rows={3}
                    placeholder="Describe what this AI system does and in which context it is deployed…"
                    {...systemForm.register('intended_purpose')}
                  />
                  {systemForm.formState.errors.intended_purpose && (
                    <p className="text-xs text-destructive">
                      {systemForm.formState.errors.intended_purpose.message}
                    </p>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Description (optional)</label>
                  <Textarea
                    rows={2}
                    placeholder="Brief internal description…"
                    {...systemForm.register('description')}
                  />
                </div>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep(1)}
                    className="flex-1"
                  >
                    Back
                  </Button>
                  <Button
                    type="button"
                    className="flex-1"
                    onClick={systemForm.handleSubmit(() => setStep(3))}
                  >
                    Next
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* ── Step 3: Risk classification ────────────────────────────────────── */}
        {step === 3 && (
          <Card>
            <CardHeader>
              <CardTitle>Risk classification</CardTitle>
              <CardDescription>
                Classify your AI system according to EU AI Act Annex III.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-5">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Risk category *</label>
                  {(
                    [
                      {
                        value: 'high_risk',
                        label: 'High Risk',
                        badge: 'destructive',
                        desc: 'Annex III system — full Annex IV documentation required',
                      },
                      {
                        value: 'limited_risk',
                        label: 'Limited Risk',
                        badge: 'secondary',
                        desc: 'Transparency obligations apply (Art. 50)',
                      },
                      {
                        value: 'minimal_risk',
                        label: 'Minimal Risk',
                        badge: 'outline',
                        desc: 'No mandatory compliance obligations',
                      },
                    ] as const
                  ).map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => riskForm.setValue('category', opt.value)}
                      className={cn(
                        'w-full text-left flex items-center gap-3 p-3 rounded-lg border transition-colors',
                        riskForm.watch('category') === opt.value
                          ? 'border-primary bg-primary/5'
                          : 'hover:border-primary/40'
                      )}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{opt.label}</span>
                          <Badge variant={opt.badge as 'destructive' | 'secondary' | 'outline'} className="text-xs">
                            {opt.value.replace('_', ' ')}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{opt.desc}</p>
                      </div>
                      {riskForm.watch('category') === opt.value && (
                        <Check className="h-4 w-4 text-primary shrink-0" />
                      )}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-3 p-3 rounded-lg border">
                  <input
                    type="checkbox"
                    id="annex_iii"
                    className="h-4 w-4 rounded"
                    {...riskForm.register('annex_iii')}
                  />
                  <label htmlFor="annex_iii" className="text-sm cursor-pointer">
                    Explicitly listed in Annex III (triggers mandatory GPAI rules)
                  </label>
                </div>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep(2)}
                    className="flex-1"
                  >
                    Back
                  </Button>
                  <Button
                    type="button"
                    disabled={isLoading}
                    className="flex-1"
                    onClick={systemForm.handleSubmit(onSubmitSystem)}
                  >
                    {isLoading ? 'Creating…' : 'Create system'}
                    {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* ── Step 4: Sample data ────────────────────────────────────────────── */}
        {step === 4 && (
          <Card>
            <CardHeader>
              <CardTitle>Jumpstart with sample data?</CardTitle>
              <CardDescription>
                Choose a pre-filled template to see how Annex IV documentation looks, or start
                with a blank file.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                {SAMPLE_DATA_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setSelectedSample(opt.id)}
                    className={cn(
                      'w-full text-left flex items-start gap-3 p-3 rounded-lg border transition-colors',
                      selectedSample === opt.id
                        ? 'border-primary bg-primary/5'
                        : 'hover:border-primary/40'
                    )}
                  >
                    <span className="text-2xl shrink-0">{opt.icon}</span>
                    <div className="flex-1">
                      <p className="font-medium text-sm">{opt.name}</p>
                      <p className="text-xs text-muted-foreground">{opt.desc}</p>
                    </div>
                    {selectedSample === opt.id && (
                      <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                    )}
                  </button>
                ))}
              </div>

              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(3)}
                  className="flex-1"
                  disabled={isLoading}
                >
                  Back
                </Button>
                <Button
                  type="button"
                  className="flex-1"
                  disabled={isLoading}
                  onClick={onApplySample}
                >
                  {isLoading
                    ? 'Applying…'
                    : selectedSample === 'none'
                    ? 'Continue without sample data'
                    : 'Apply & continue'}
                  {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── Step 5: Done ──────────────────────────────────────────────────── */}
        {step === 5 && (
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                <Check className="h-8 w-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl">You&apos;re all set! 🎉</CardTitle>
              <CardDescription className="text-base">
                Your AI system has been created
                {selectedSample !== 'none' ? ' and pre-filled with sample data' : ''}. Start
                filling in the Annex IV Technical File or let the AI Copilot help you draft it.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-lg border bg-muted/30 p-4 text-sm space-y-2">
                <p className="font-medium">What to do next:</p>
                <ul className="space-y-1 text-muted-foreground text-xs list-disc list-inside">
                  <li>Open your AI system and review the 9 Annex IV sections</li>
                  <li>Use the AI Copilot to draft missing sections</li>
                  <li>Upload supporting evidence (model cards, test reports, etc.)</li>
                  <li>Export a PDF when you&apos;re ready for review</li>
                </ul>
              </div>
              <Button className="w-full" size="lg" onClick={goToSystem}>
                Open AI system
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button variant="outline" className="w-full" onClick={goToDashboard}>
                Go to dashboard
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
