'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart3,
  Cpu,
  DollarSign,
  Zap,
  TrendingUp,
  CheckCircle2,
  XCircle,
  RefreshCw,
} from 'lucide-react'
import { llmUsageApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { formatDate } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import type { LLMUsageStats, LLMFeatureStat } from '@/types'

const PERIOD_OPTIONS = [
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' },
]

function formatCost(usd: number): string {
  if (usd < 0.001) return '$0.00'
  if (usd < 1) return `$${usd.toFixed(4)}`
  return `$${usd.toFixed(2)}`
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

function KPICard({
  icon: Icon,
  label,
  value,
  sub,
  variant = 'default',
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  sub?: string
  variant?: 'default' | 'cost'
}) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-start gap-3">
          <div
            className={`p-2 rounded-md ${variant === 'cost' ? 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-primary/10 text-primary'}`}
          >
            <Icon className="h-4 w-4" />
          </div>
          <div>
            <p className="text-2xl font-bold">{value}</p>
            <p className="text-xs text-muted-foreground">{label}</p>
            {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function FeatureTable({
  title,
  data,
}: {
  title: string
  data: Record<string, LLMFeatureStat>
}) {
  const rows = Object.entries(data).sort((a, b) => b[1].cost_usd - a[1].cost_usd)
  if (rows.length === 0) return null

  const maxCost = Math.max(...rows.map(([, s]) => s.cost_usd), 0.0001)

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {rows.map(([name, stats]) => (
            <div key={name} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium font-mono">{name}</span>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{stats.calls} calls</span>
                  <span>{formatNumber(stats.tokens)} tokens</span>
                  <span className="font-medium text-foreground">{formatCost(stats.cost_usd)}</span>
                </div>
              </div>
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full"
                  style={{ width: `${(stats.cost_usd / maxCost) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default function LLMUsagePage() {
  const { currentOrg } = useAuthStore()
  const [days, setDays] = useState('30')

  const {
    data: usage,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['llm-usage', currentOrg?.id, days],
    queryFn: () =>
      llmUsageApi.getOrgUsage(currentOrg!.id, parseInt(days)).then((r) => r.data),
    enabled: !!currentOrg,
    staleTime: 60_000,
  })

  if (!currentOrg) {
    return <p className="text-muted-foreground">Loading organisation…</p>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            AI Usage &amp; Costs
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Track token consumption and estimated costs for all AI-powered features.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={days} onValueChange={setDays}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PERIOD_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {isLoading && (
        <div className="space-y-4 animate-pulse">
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-muted rounded-lg" />
            ))}
          </div>
          <div className="h-48 bg-muted rounded-lg" />
        </div>
      )}

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-4 text-destructive">
            Failed to load usage data. You may not have permission to view this.
          </CardContent>
        </Card>
      )}

      {usage && (
        <>
          {/* Period info */}
          <p className="text-xs text-muted-foreground">
            Period: {formatDate(usage.period_start)} — {formatDate(usage.period_end)}
          </p>

          {/* KPI cards */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <KPICard
              icon={DollarSign}
              label="Estimated cost"
              value={formatCost(usage.summary.total_cost_usd)}
              variant="cost"
            />
            <KPICard
              icon={Zap}
              label="Total API calls"
              value={formatNumber(usage.summary.total_calls)}
              sub={`${usage.summary.successful_calls} succeeded`}
            />
            <KPICard
              icon={Cpu}
              label="Total tokens"
              value={formatNumber(usage.summary.total_tokens)}
              sub={`${formatNumber(usage.summary.total_prompt_tokens)} prompt + ${formatNumber(usage.summary.total_completion_tokens)} completion`}
            />
            <KPICard
              icon={TrendingUp}
              label="Success rate"
              value={
                usage.summary.total_calls > 0
                  ? `${Math.round((usage.summary.successful_calls / usage.summary.total_calls) * 100)}%`
                  : '—'
              }
              sub={`${usage.summary.failed_calls} failed`}
            />
          </div>

          {/* Call breakdown */}
          <div className="flex gap-4">
            <div className="flex items-center gap-1.5 text-sm">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="font-medium">{usage.summary.successful_calls}</span>
              <span className="text-muted-foreground">successful</span>
            </div>
            {usage.summary.failed_calls > 0 && (
              <div className="flex items-center gap-1.5 text-sm">
                <XCircle className="h-4 w-4 text-red-500" />
                <span className="font-medium">{usage.summary.failed_calls}</span>
                <span className="text-muted-foreground">failed</span>
              </div>
            )}
          </div>

          {/* Feature & model breakdowns */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <FeatureTable title="By Feature" data={usage.by_feature} />
            <FeatureTable title="By Model" data={usage.by_model} />
          </div>

          {Object.keys(usage.by_feature).length === 0 && (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No AI usage recorded in the selected period.</p>
                <p className="text-xs mt-1">
                  Start using AI Copilot features to see usage data here.
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
