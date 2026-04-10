'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Check, Zap, ShieldCheck, Building2, ExternalLink } from 'lucide-react'
import { billingApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/use-toast'
import { formatDate } from '@/lib/utils'

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    icon: ShieldCheck,
    price: '€49',
    period: '/month',
    description: 'For small teams getting started with EU AI Act compliance.',
    features: [
      'Up to 3 AI systems',
      'Annex IV Technical File',
      'PDF & Markdown export',
      'AI Copilot (50 drafts/month)',
      'Email support',
    ],
    highlighted: false,
  },
  {
    id: 'pro',
    name: 'Pro',
    icon: Zap,
    price: '€149',
    period: '/month',
    description: 'For growing teams with multiple AI systems.',
    features: [
      'Unlimited AI systems',
      'Annex IV + Annex III assessment',
      'PDF & Markdown export',
      'AI Copilot (unlimited)',
      'Q&A over Technical File',
      'Revision history & diff',
      'Priority support',
      'API access',
    ],
    highlighted: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    icon: Building2,
    price: 'Custom',
    period: '',
    description: 'For large organisations and compliance consultancies.',
    features: [
      'Everything in Pro',
      'Custom integrations (GitHub, MLflow)',
      'SSO / SAML',
      'Audit log',
      'Dedicated compliance manager',
      'Custom SLA',
      'On-premise option',
    ],
    highlighted: false,
  },
]

export default function BillingPage() {
  const currentOrg = useAuthStore((s) => s.currentOrg)

  const { data: billing, refetch } = useQuery({
    queryKey: ['billing-status', currentOrg?.id],
    queryFn: () => billingApi.status(currentOrg!.id).then((r) => r.data),
    enabled: !!currentOrg,
  })

  const checkoutMutation = useMutation({
    mutationFn: (plan: string) => billingApi.createCheckout(currentOrg!.id, plan).then((r) => r.data),
    onSuccess: ({ url }) => {
      window.location.href = url
    },
    onError: () =>
      toast({ variant: 'destructive', title: 'Could not start checkout. Please try again.' }),
  })

  const portalMutation = useMutation({
    mutationFn: () => billingApi.createPortal(currentOrg!.id).then((r) => r.data),
    onSuccess: ({ url }) => {
      window.open(url, '_blank')
    },
    onError: () =>
      toast({ variant: 'destructive', title: 'Could not open billing portal.' }),
  })

  const isCurrentPlan = (planId: string) => billing?.plan === planId && billing?.has_active_subscription

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Billing & Plans</h1>
        <p className="text-muted-foreground text-sm">
          Manage your CompliAI subscription and billing details.
        </p>
      </div>

      {/* Current status */}
      {billing && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Current Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-6 text-sm">
              <div>
                <p className="text-muted-foreground">Plan</p>
                <p className="font-medium capitalize">{billing.plan}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p className="font-medium">
                  {billing.has_active_subscription ? (
                    <Badge variant="default">Active</Badge>
                  ) : billing.trial_active ? (
                    <Badge variant="secondary">Trial — {billing.trial_days_remaining} days left</Badge>
                  ) : (
                    <Badge variant="destructive">Expired</Badge>
                  )}
                </p>
              </div>
              {billing.trial_ends_at && !billing.has_active_subscription && (
                <div>
                  <p className="text-muted-foreground">Trial ends</p>
                  <p className="font-medium">{formatDate(billing.trial_ends_at)}</p>
                </div>
              )}
              {billing.has_active_subscription && (
                <div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => portalMutation.mutate()}
                    disabled={portalMutation.isPending}
                    className="gap-1.5"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    Manage subscription
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Plan cards */}
      <div className="grid gap-6 md:grid-cols-3">
        {PLANS.map((plan) => {
          const Icon = plan.icon
          const isCurrent = isCurrentPlan(plan.id)
          return (
            <Card
              key={plan.id}
              className={
                plan.highlighted
                  ? 'border-primary shadow-md relative'
                  : ''
              }
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-primary text-primary-foreground">Most popular</Badge>
                </div>
              )}
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Icon className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">{plan.name}</CardTitle>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground text-sm">{plan.period}</span>
                </div>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <Check className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                {plan.id === 'enterprise' ? (
                  <a
                    href="mailto:sales@compliai.app"
                    className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 w-full"
                  >
                    Contact sales
                  </a>
                ) : isCurrent ? (
                  <Button disabled className="w-full">
                    Current plan
                  </Button>
                ) : (
                  <Button
                    variant={plan.highlighted ? 'default' : 'outline'}
                    className="w-full"
                    onClick={() => checkoutMutation.mutate(plan.id)}
                    disabled={checkoutMutation.isPending}
                  >
                    {checkoutMutation.isPending ? 'Redirecting…' : 'Get started'}
                  </Button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      <p className="text-xs text-muted-foreground text-center">
        All prices exclude VAT. Secure payments via Stripe. Cancel anytime.
      </p>
    </div>
  )
}
