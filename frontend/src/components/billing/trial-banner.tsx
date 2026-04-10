'use client'

import { AlertTriangle, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { billingApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export function TrialBanner() {
  const currentOrg = useAuthStore((s) => s.currentOrg)

  const { data: billing } = useQuery({
    queryKey: ['billing-status', currentOrg?.id],
    queryFn: () => billingApi.status(currentOrg!.id).then((r) => r.data),
    enabled: !!currentOrg,
    refetchInterval: 60_000, // refresh every minute
  })

  if (!billing) return null
  if (billing.has_active_subscription) return null
  if (!billing.trial_active && !billing.trial_ends_at) return null

  const daysLeft = billing.trial_days_remaining ?? 0
  const isExpired = !billing.trial_active
  const isExpiringSoon = billing.trial_active && daysLeft <= 3

  if (!isExpired && !isExpiringSoon) return null

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3 px-4 py-2 text-sm',
        isExpired
          ? 'bg-destructive/10 text-destructive border-b border-destructive/20'
          : 'bg-yellow-50 text-yellow-800 border-b border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400'
      )}
    >
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        {isExpired ? (
          <span>
            <strong>Trial expired.</strong> Upgrade to continue editing your Technical File.
          </span>
        ) : (
          <span>
            <strong>{daysLeft} day{daysLeft !== 1 ? 's' : ''} left</strong> in your free trial.
          </span>
        )}
      </div>
      <Link href="/dashboard/billing">
        <Button
          size="sm"
          variant={isExpired ? 'destructive' : 'default'}
          className="h-7 text-xs"
        >
          Upgrade plan
        </Button>
      </Link>
    </div>
  )
}
