'use client'

import { Lock } from 'lucide-react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { billingApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface UpgradeGateProps {
  children: React.ReactNode
  /** Feature name shown in the gate message */
  feature?: string
}

/**
 * Wraps content that requires an active subscription or trial.
 * Renders a lock overlay if billing access is not available.
 */
export function UpgradeGate({ children, feature }: UpgradeGateProps) {
  const currentOrg = useAuthStore((s) => s.currentOrg)

  const { data: billing, isLoading } = useQuery({
    queryKey: ['billing-status', currentOrg?.id],
    queryFn: () => billingApi.status(currentOrg!.id).then((r) => r.data),
    enabled: !!currentOrg,
  })

  // While loading, show content (assume access to avoid flash)
  if (isLoading || !billing) return <>{children}</>

  // Access granted
  if (billing.has_billing_access) return <>{children}</>

  // Access denied
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-16 text-center gap-4">
        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center">
          <Lock className="h-6 w-6 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <h3 className="font-semibold text-base">
            {feature ? `${feature} requires an active plan` : 'Upgrade to access this feature'}
          </h3>
          <p className="text-sm text-muted-foreground max-w-xs">
            Your free trial has expired. Upgrade to continue managing your EU AI Act compliance.
          </p>
        </div>
        <Link href="/dashboard/billing">
          <Button>View plans</Button>
        </Link>
      </CardContent>
    </Card>
  )
}
