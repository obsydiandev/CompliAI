'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { ShieldAlert, ShieldCheck, AlertTriangle, BarChart3, ArrowRight } from 'lucide-react'
import { useAuthStore } from '@/lib/auth'
import { systemApi, policyApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import type { AISystem, ComplianceHealthReport } from '@/types'

function RiskHeatCell({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  let bg = 'bg-green-100 text-green-800'
  if (pct < 50) bg = 'bg-red-100 text-red-800'
  else if (pct < 80) bg = 'bg-yellow-100 text-yellow-800'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${bg}`}>
      {pct}%
    </span>
  )
}

function SystemRow({
  system,
  health,
}: {
  system: AISystem
  health: ComplianceHealthReport | undefined
}) {
  const violations = health?.open_violations ?? 0
  const completeness = health?.overall_completeness ?? 0

  return (
    <tr className="border-b hover:bg-muted/20">
      <td className="px-4 py-3">
        <Link
          href={`/systems/${system.id}`}
          className="font-medium hover:underline"
        >
          {system.name}
        </Link>
        <p className="text-xs text-muted-foreground mt-0.5">{system.category}</p>
      </td>
      <td className="px-4 py-3">
        <RiskHeatCell value={completeness} />
      </td>
      <td className="px-4 py-3">
        {violations === 0 ? (
          <span className="inline-flex items-center gap-1 text-green-600 text-xs">
            <ShieldCheck className="h-3 w-3" /> Clean
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-red-600 text-xs">
            <AlertTriangle className="h-3 w-3" /> {violations} open
          </span>
        )}
      </td>
      <td className="px-4 py-3 text-xs text-muted-foreground">
        {health?.days_since_last_revision != null
          ? `${health.days_since_last_revision}d ago`
          : '—'}
      </td>
      <td className="px-4 py-3 text-xs text-muted-foreground">
        {health?.unlinked_deployments ?? 0}
      </td>
      <td className="px-4 py-3">
        <Link href={`/systems/${system.id}/compliance`}>
          <Button variant="ghost" size="sm">
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </td>
    </tr>
  )
}

export default function PortfolioPage() {
  const currentOrg = useAuthStore((s) => s.currentOrg)

  const { data: systems = [], isLoading } = useQuery({
    queryKey: ['systems', currentOrg?.id],
    queryFn: () => systemApi.list(currentOrg!.id).then((r) => r.data),
    enabled: !!currentOrg,
  })

  // Fetch health data for all systems (parallel queries)
  const healthQueries = systems.map((sys: AISystem) => ({
    id: sys.id,
    query: useQuery({  // eslint-disable-line react-hooks/rules-of-hooks
      queryKey: ['compliance-health', sys.id],
      queryFn: () => policyApi.health(sys.id).then((r) => r.data),
      retry: false,
    }),
  }))

  const healthMap = new Map<string, ComplianceHealthReport>()
  healthQueries.forEach(({ id, query }) => {
    if (query.data) healthMap.set(id, query.data)
  })

  // Portfolio-level aggregates
  const totalSystems = systems.length
  const totalViolations = Array.from(healthMap.values()).reduce(
    (sum, h) => sum + h.open_violations,
    0,
  )
  const avgCompleteness =
    healthMap.size > 0
      ? Array.from(healthMap.values()).reduce((sum, h) => sum + h.overall_completeness, 0) /
        healthMap.size
      : 0
  const systemsAtRisk = Array.from(healthMap.values()).filter(
    (h) => h.open_violations > 0 || (h.days_since_last_revision ?? 0) > 30,
  ).length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Portfolio Overview</h1>
        <p className="text-muted-foreground text-sm">
          Compliance status across all AI systems in {currentOrg?.name}
        </p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Total Systems</p>
            <p className="text-3xl font-bold">{totalSystems}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Avg Completeness</p>
            <p className="text-3xl font-bold">{Math.round(avgCompleteness * 100)}%</p>
            <Progress value={Math.round(avgCompleteness * 100)} className="h-1.5 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-1">
              {totalViolations === 0 ? (
                <ShieldCheck className="h-4 w-4 text-green-500" />
              ) : (
                <ShieldAlert className="h-4 w-4 text-destructive" />
              )}
              <p className="text-xs text-muted-foreground">Open Violations</p>
            </div>
            <p className="text-3xl font-bold">{totalViolations}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Systems at Risk</p>
            <p className="text-3xl font-bold text-destructive">{systemsAtRisk}</p>
            <p className="text-xs text-muted-foreground">of {totalSystems}</p>
          </CardContent>
        </Card>
      </div>

      {/* Risk heatmap table */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Heatmap</CardTitle>
          <CardDescription>Compliance status per AI system</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="h-32 flex items-center justify-center text-muted-foreground text-sm">
              Loading…
            </div>
          ) : systems.length === 0 ? (
            <div className="h-32 flex flex-col items-center justify-center gap-3">
              <p className="text-muted-foreground text-sm">No AI systems yet.</p>
              <Link href="/systems/new">
                <Button size="sm">Add first system</Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/40">
                    <th className="px-4 py-3 text-left font-medium">System</th>
                    <th className="px-4 py-3 text-left font-medium">Completeness</th>
                    <th className="px-4 py-3 text-left font-medium">Violations</th>
                    <th className="px-4 py-3 text-left font-medium">Last Revision</th>
                    <th className="px-4 py-3 text-left font-medium">Unlinked Deploys</th>
                    <th className="px-4 py-3 text-left font-medium" />
                  </tr>
                </thead>
                <tbody>
                  {systems.map((sys: AISystem) => (
                    <SystemRow
                      key={sys.id}
                      system={sys}
                      health={healthMap.get(sys.id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
