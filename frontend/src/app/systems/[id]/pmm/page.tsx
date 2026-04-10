'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Plus,
  TrendingUp,
  Clock,
  Save,
} from 'lucide-react'
import { pmmApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/components/ui/use-toast'
import type { PMMPlanUpdate, MetricEntry } from '@/types'

function CompletionIcon({ done }: { done: boolean }) {
  return done ? (
    <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
  ) : (
    <XCircle className="h-4 w-4 text-red-400 shrink-0" />
  )
}

function MetricEntryForm({
  onSubmit,
  isLoading,
}: {
  onSubmit: (metrics: MetricEntry[]) => void
  isLoading: boolean
}) {
  const [entries, setEntries] = useState<MetricEntry[]>([
    { metric_name: '', value: 0, unit: '', notes: '' },
  ])

  const addEntry = () =>
    setEntries((prev) => [...prev, { metric_name: '', value: 0, unit: '', notes: '' }])

  const updateEntry = (index: number, field: keyof MetricEntry, value: string | number) => {
    setEntries((prev) =>
      prev.map((e, i) => (i === index ? { ...e, [field]: value } : e))
    )
  }

  const removeEntry = (index: number) =>
    setEntries((prev) => prev.filter((_, i) => i !== index))

  const handleSubmit = () => {
    const valid = entries.filter((e) => e.metric_name.trim())
    if (valid.length === 0) {
      toast({ variant: 'destructive', title: 'Enter at least one metric name.' })
      return
    }
    onSubmit(valid)
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, idx) => (
        <div key={idx} className="grid grid-cols-4 gap-2 items-end">
          <div className="col-span-2 space-y-1">
            <Label className="text-xs">Metric name</Label>
            <Input
              placeholder="e.g. accuracy"
              value={entry.metric_name}
              onChange={(e) => updateEntry(idx, 'metric_name', e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Value</Label>
            <Input
              type="number"
              step="any"
              value={entry.value}
              onChange={(e) => updateEntry(idx, 'value', parseFloat(e.target.value) || 0)}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Unit</Label>
            <div className="flex gap-1">
              <Input
                placeholder="e.g. %"
                value={entry.unit || ''}
                onChange={(e) => updateEntry(idx, 'unit', e.target.value)}
              />
              {entries.length > 1 && (
                <Button
                  variant="outline"
                  size="icon"
                  className="shrink-0"
                  onClick={() => removeEntry(idx)}
                >
                  ✕
                </Button>
              )}
            </div>
          </div>
        </div>
      ))}
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={addEntry}>
          <Plus className="h-3 w-3 mr-1" />
          Add metric
        </Button>
        <Button size="sm" onClick={handleSubmit} disabled={isLoading}>
          {isLoading ? 'Saving…' : 'Record metrics'}
        </Button>
      </div>
    </div>
  )
}

export default function PMMPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [draftPlan, setDraftPlan] = useState('')
  const [draftProcedure, setDraftProcedure] = useState('')
  const [draftFrequency, setDraftFrequency] = useState('')
  const [showMetricsForm, setShowMetricsForm] = useState(false)

  const { data: pmm, isLoading } = useQuery({
    queryKey: ['pmm', id],
    queryFn: () => pmmApi.get(id).then((r) => r.data),
  })

  // Initialize draft fields from loaded PMM data — only when pmm changes and not in edit mode
  useEffect(() => {
    if (pmm && !editing) {
      setDraftPlan(String(pmm.content.pmm_plan || ''))
      setDraftProcedure(String(pmm.content.incident_reporting_procedure || ''))
      setDraftFrequency(String(pmm.content.reporting_frequency || ''))
    }
  }, [pmm, editing])

  const { data: metricsLog } = useQuery({
    queryKey: ['pmm-metrics', id],
    queryFn: () => pmmApi.listMetrics(id).then((r) => r.data),
  })

  const { data: summary } = useQuery({
    queryKey: ['pmm-summary', id],
    queryFn: () => pmmApi.summary(id).then((r) => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: (data: PMMPlanUpdate) => pmmApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pmm', id] })
      qc.invalidateQueries({ queryKey: ['pmm-summary', id] })
      setEditing(false)
      toast({ title: 'PMM plan updated' })
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to update PMM plan' }),
  })

  const metricsMutation = useMutation({
    mutationFn: (metrics: MetricEntry[]) => pmmApi.submitMetrics(id, metrics),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['pmm-metrics', id] })
      setShowMetricsForm(false)
      toast({ title: `Recorded ${data.data.recorded_entries} metric(s)` })
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to record metrics' }),
  })

  const handleSave = () => {
    updateMutation.mutate({
      pmm_plan: draftPlan || undefined,
      incident_reporting_procedure: draftProcedure || undefined,
      reporting_frequency: draftFrequency || undefined,
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-muted rounded w-64" />
        <div className="h-32 bg-muted rounded" />
      </div>
    )
  }

  const completionPct = Math.round((summary?.completeness ?? 0) * 100)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link
          href={`/systems/${id}`}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to system
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6" />
            Post-Market Monitoring
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Monitor system performance, manage the PMM plan, and log metrics after deployment.
          </p>
        </div>
        <Badge
          variant={completionPct >= 80 ? 'default' : completionPct >= 40 ? 'secondary' : 'destructive'}
          className="text-sm px-3 py-1"
        >
          {completionPct}% complete
        </Badge>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4 space-y-1">
            <div className="flex items-center gap-2">
              <CompletionIcon done={summary?.has_plan ?? false} />
              <span className="text-sm font-medium">PMM Plan</span>
            </div>
            <p className="text-xs text-muted-foreground pl-6">
              {summary?.has_plan ? 'Plan documented' : 'Missing — required for compliance'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 space-y-1">
            <div className="flex items-center gap-2">
              <CompletionIcon done={summary?.has_metrics ?? false} />
              <span className="text-sm font-medium">Monitoring Metrics</span>
            </div>
            <p className="text-xs text-muted-foreground pl-6">
              {summary?.has_metrics ? 'Metrics defined' : 'Missing — required for compliance'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 space-y-1">
            <div className="flex items-center gap-2">
              <CompletionIcon done={summary?.has_incident_procedure ?? false} />
              <span className="text-sm font-medium">Incident Procedure</span>
            </div>
            <p className="text-xs text-muted-foreground pl-6">
              {summary?.has_incident_procedure
                ? 'Procedure defined'
                : 'Missing — required for compliance'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Section 9 completeness */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Section 9 Completeness</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Progress value={completionPct} className="h-2" />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{completionPct}% complete</span>
            {summary?.last_section_updated_at && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Last updated {formatDate(summary.last_section_updated_at)}
              </span>
            )}
          </div>
          {(summary?.missing_fields ?? []).length > 0 && (
            <div className="flex items-start gap-1.5 text-sm text-yellow-600 dark:text-yellow-400 mt-2">
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>
                Missing required fields: {summary!.missing_fields.join(', ')}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* PMM Plan editor */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">PMM Plan</CardTitle>
              <CardDescription>
                Describe how this system will be monitored after deployment.
              </CardDescription>
            </div>
            {!editing ? (
              <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                Edit
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                >
                  <Save className="h-4 w-4 mr-1" />
                  {updateMutation.isPending ? 'Saving…' : 'Save'}
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <Label>Post-Market Monitoring Plan</Label>
            {editing ? (
              <Textarea
                rows={5}
                placeholder="Describe the PMM plan narrative…"
                value={draftPlan}
                onChange={(e) => setDraftPlan(e.target.value)}
              />
            ) : (
              <p className="text-sm text-muted-foreground whitespace-pre-wrap min-h-[2rem]">
                {String(pmm?.content.pmm_plan || '') || (
                  <span className="italic">Not provided</span>
                )}
              </p>
            )}
          </div>
          <div className="space-y-1">
            <Label>Incident Reporting Procedure</Label>
            {editing ? (
              <Textarea
                rows={3}
                placeholder="Describe how incidents are reported to authorities…"
                value={draftProcedure}
                onChange={(e) => setDraftProcedure(e.target.value)}
              />
            ) : (
              <p className="text-sm text-muted-foreground whitespace-pre-wrap min-h-[2rem]">
                {String(pmm?.content.incident_reporting_procedure || '') || (
                  <span className="italic">Not provided</span>
                )}
              </p>
            )}
          </div>
          <div className="space-y-1">
            <Label>Reporting Frequency</Label>
            {editing ? (
              <Input
                placeholder="e.g. Quarterly, Monthly"
                value={draftFrequency}
                onChange={(e) => setDraftFrequency(e.target.value)}
              />
            ) : (
              <p className="text-sm text-muted-foreground">
                {String(pmm?.content.reporting_frequency || '') || (
                  <span className="italic">Not provided</span>
                )}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Metrics log */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Monitoring Metrics Log
              </CardTitle>
              <CardDescription>
                Record metrics snapshots to track system performance over time.
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowMetricsForm(!showMetricsForm)}
            >
              <Plus className="h-4 w-4 mr-1" />
              Record metrics
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {showMetricsForm && (
            <div className="border rounded-md p-4 bg-muted/30 space-y-3">
              <p className="text-sm font-medium">New metrics snapshot</p>
              <MetricEntryForm
                onSubmit={(metrics) => metricsMutation.mutate(metrics)}
                isLoading={metricsMutation.isPending}
              />
            </div>
          )}

          {!metricsLog || metricsLog.total_entries === 0 ? (
            <p className="text-sm text-muted-foreground">No metrics recorded yet.</p>
          ) : (
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground">
                {metricsLog.total_entries} snapshot{metricsLog.total_entries !== 1 ? 's' : ''}{' '}
                recorded
              </p>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {[...metricsLog.entries].reverse().map((entry, idx) => (
                  <div key={idx} className="border rounded-md p-3 space-y-2">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatDate(entry.recorded_at)}
                    </div>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                      {entry.metrics.map((m, mi) => (
                        <div
                          key={mi}
                          className="bg-muted rounded-md px-2 py-1 text-center"
                        >
                          <div className="text-base font-semibold">
                            {m.value}
                            {m.unit && (
                              <span className="text-xs font-normal ml-0.5">{m.unit}</span>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground truncate">{m.metric_name}</div>
                        </div>
                      ))}
                    </div>
                    {entry.metrics.some((m) => m.notes) && (
                      <p className="text-xs text-muted-foreground">
                        {entry.metrics.find((m) => m.notes)?.notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
