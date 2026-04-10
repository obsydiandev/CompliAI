'use client'

import { useQuery } from '@tanstack/react-query'
import {
  Building2,
  Cpu,
  ShieldAlert,
  TrendingUp,
  Users,
  CreditCard,
  AlertTriangle,
  BarChart3,
} from 'lucide-react'
import { adminApi } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import type { FounderMetrics } from '@/types'

function KpiCard({
  icon: Icon,
  label,
  value,
  sub,
  highlight,
}: {
  icon: React.ElementType
  label: string
  value: string | number
  sub?: string
  highlight?: 'red' | 'green' | 'yellow'
}) {
  const iconColor =
    highlight === 'red'
      ? 'text-destructive'
      : highlight === 'green'
      ? 'text-green-600'
      : highlight === 'yellow'
      ? 'text-yellow-600'
      : 'text-muted-foreground'

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-2 mb-1">
          <Icon className={`h-4 w-4 ${iconColor}`} />
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
        <p className="text-3xl font-bold">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  )
}

export default function FounderMetricsPage() {
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: () => adminApi.metrics().then((r) => r.data as FounderMetrics),
    refetchInterval: 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-destructive">
        <AlertTriangle className="h-5 w-5" />
        <span>Failed to load metrics. Superuser access required.</span>
      </div>
    )
  }

  if (!metrics) return null

  const { orgs, systems, compliance, growth } = metrics

  return (
    <div className="space-y-8 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold">Platform Metrics</h1>
        <p className="text-muted-foreground text-sm">
          Last updated:{' '}
          {new Date(metrics.generated_at).toLocaleString()}
        </p>
      </div>

      {/* Org metrics */}
      <section>
        <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
          <Building2 className="h-4 w-4 text-primary" />
          Organisations
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard icon={Building2} label="Total Orgs" value={orgs.total} />
          <KpiCard
            icon={CreditCard}
            label="Paid"
            value={orgs.paid}
            sub={`of ${orgs.total}`}
            highlight={orgs.paid > 0 ? 'green' : undefined}
          />
          <KpiCard
            icon={Users}
            label="Active Trials"
            value={orgs.active_trials}
          />
          <div>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">Plan Breakdown</span>
                </div>
                <div className="space-y-1.5 mt-2">
                  {([
                    ['starter', orgs.plan_breakdown.starter],
                    ['pro', orgs.plan_breakdown.pro],
                    ['enterprise', orgs.plan_breakdown.enterprise],
                  ] as [string, number][]).map(([plan, count]) => (
                    <div key={plan} className="flex items-center gap-2 text-xs">
                      <Badge variant="outline" className="capitalize w-20 justify-center text-xs">
                        {plan}
                      </Badge>
                      <Progress value={(count / Math.max(orgs.total, 1)) * 100} className="h-1.5 flex-1" />
                      <span className="w-6 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* System metrics */}
      <section>
        <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
          <Cpu className="h-4 w-4 text-primary" />
          AI Systems
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard icon={Cpu} label="Total Systems" value={systems.total} />
          <KpiCard
            icon={ShieldAlert}
            label="High Risk"
            value={systems.high_risk}
            highlight={systems.high_risk > 0 ? 'yellow' : undefined}
          />
          <KpiCard icon={Cpu} label="Limited Risk" value={systems.limited_risk} />
          <KpiCard
            icon={BarChart3}
            label="Avg Completeness"
            value={`${systems.avg_completeness_pct}%`}
            highlight={
              systems.avg_completeness_pct >= 80
                ? 'green'
                : systems.avg_completeness_pct >= 50
                ? 'yellow'
                : 'red'
            }
          />
        </div>
      </section>

      {/* Compliance metrics */}
      <section>
        <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-primary" />
          Compliance
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <KpiCard
            icon={AlertTriangle}
            label="Open Violations"
            value={compliance.total_open_violations}
            highlight={compliance.total_open_violations > 0 ? 'red' : 'green'}
          />
          <KpiCard
            icon={ShieldAlert}
            label="Systems at Risk"
            value={compliance.systems_at_risk}
            sub={`of ${systems.total} total`}
            highlight={compliance.systems_at_risk > 0 ? 'red' : 'green'}
          />
        </div>
      </section>

      {/* Growth metrics */}
      <section>
        <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          Growth (Last 30 Days)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <KpiCard
            icon={Building2}
            label="New Organisations"
            value={growth.new_orgs_last_30d}
            highlight={growth.new_orgs_last_30d > 0 ? 'green' : undefined}
          />
          <KpiCard
            icon={Cpu}
            label="New AI Systems"
            value={growth.new_systems_last_30d}
            highlight={growth.new_systems_last_30d > 0 ? 'green' : undefined}
          />
        </div>
      </section>
    </div>
  )
}
