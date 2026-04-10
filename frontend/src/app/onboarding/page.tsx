'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ShieldCheck, ArrowRight, Check } from 'lucide-react'
import { systemApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/components/ui/use-toast'
import { cn } from '@/lib/utils'

const STEPS = [
  { id: 1, title: 'Welcome', description: 'Get started with CompliAI' },
  { id: 2, title: 'Your first AI system', description: 'Tell us about your AI system' },
  { id: 3, title: "You're all set", description: 'Start your compliance journey' },
]

const systemSchema = z.object({
  name: z.string().min(2, 'System name must be at least 2 characters'),
  description: z.string().optional(),
  intended_purpose: z.string().min(10, 'Please describe the intended purpose (min 10 characters)'),
  category: z.enum(['high_risk', 'limited_risk', 'minimal_risk']),
})

type SystemForm = z.infer<typeof systemSchema>

export default function OnboardingPage() {
  const router = useRouter()
  const currentOrg = useAuthStore((s) => s.currentOrg)
  const [step, setStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [createdSystemId, setCreatedSystemId] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SystemForm>({
    resolver: zodResolver(systemSchema),
    defaultValues: { category: 'high_risk' },
  })

  async function onSubmitSystem(data: SystemForm) {
    if (!currentOrg) {
      toast({ variant: 'destructive', title: 'No organisation found' })
      return
    }
    setIsLoading(true)
    try {
      const res = await systemApi.create({
        org_id: currentOrg.id,
        name: data.name,
        description: data.description,
        intended_purpose: data.intended_purpose,
        category: data.category,
      })
      setCreatedSystemId(res.data.id)
      setStep(3)
    } catch {
      toast({ variant: 'destructive', title: 'Failed to create AI system' })
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
        <div className="flex items-center justify-center gap-2">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-2">
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
                    'h-0.5 w-12 transition-colors',
                    step > s.id ? 'bg-primary' : 'bg-muted-foreground/20'
                  )}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step content */}
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
              <div className="grid gap-4 sm:grid-cols-3">
                {[
                  {
                    icon: '📋',
                    title: 'Annex IV Technical File',
                    desc: 'Auto-generate all 9 sections required by Art. 11',
                  },
                  {
                    icon: '🤖',
                    title: 'AI Copilot',
                    desc: 'Drafts, suggestions & Q&A powered by GPT-4o',
                  },
                  {
                    icon: '📄',
                    title: 'Export & Share',
                    desc: 'PDF, Markdown, and JSON export in one click',
                  },
                ].map((item) => (
                  <div
                    key={item.title}
                    className="flex flex-col items-center text-center p-4 rounded-lg border bg-muted/30 space-y-2"
                  >
                    <span className="text-2xl">{item.icon}</span>
                    <p className="font-medium text-sm">{item.title}</p>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
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

        {step === 2 && (
          <Card>
            <CardHeader>
              <CardTitle>Add your first AI system</CardTitle>
              <CardDescription>
                Tell us about the AI system you need to document. You can add more later.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmitSystem)} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium">System name *</label>
                  <Input placeholder="e.g. Credit Risk Scorer v2" {...register('name')} />
                  {errors.name && (
                    <p className="text-xs text-destructive">{errors.name.message}</p>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Intended purpose *</label>
                  <Textarea
                    rows={3}
                    placeholder="Describe what this AI system does and in which context it is deployed…"
                    {...register('intended_purpose')}
                  />
                  {errors.intended_purpose && (
                    <p className="text-xs text-destructive">{errors.intended_purpose.message}</p>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Risk category</label>
                  <select
                    className="w-full border rounded-md h-9 px-3 text-sm bg-background"
                    {...register('category')}
                  >
                    <option value="high_risk">High Risk (Annex III)</option>
                    <option value="limited_risk">Limited Risk</option>
                    <option value="minimal_risk">Minimal Risk</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Description (optional)</label>
                  <Textarea
                    rows={2}
                    placeholder="Brief internal description…"
                    {...register('description')}
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
                  <Button type="submit" disabled={isLoading} className="flex-1">
                    {isLoading ? 'Creating…' : 'Create system'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {step === 3 && (
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                <Check className="h-8 w-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl">You&apos;re all set! 🎉</CardTitle>
              <CardDescription className="text-base">
                Your AI system has been created. Start filling in the Annex IV Technical File or
                let the AI Copilot help you draft it.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
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
