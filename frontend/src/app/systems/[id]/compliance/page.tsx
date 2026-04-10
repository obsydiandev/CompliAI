'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ShieldCheck,
  ShieldAlert,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Play,
  BarChart3,
  FileSearch,
  Wand2,
  Loader2,
} from 'lucide-react'
import { policyApi, ruleGeneratorApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { formatDate } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/use-toast'
import type { ComplianceHealthReport, ComplianceEvent, SectionDebt, GeneratedRule } from '@/types'

function SeverityBadge({ severity }: { severity: string }) {
  if (severity === 'blocking')
    return <Badge variant="destructive">Blocking</Badge>
  if (severity === 'warning')
    return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Warning</Badge>
  return <Badge variant="outline">Info</Badge>
}

function HealthScoreBadge({ score }: { score: number }) {
  if (score >= 0.8) return <Badge className="bg-green-100 text-green-800 border-green-200">Healthy</Badge>
  if (score >= 0.5) return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Needs Attention</Badge>
  return <Badge variant="destructive">At Risk</Badge>
}

function SectionDebtRow({ sec }: { sec: SectionDebt }) {
  const pct = Math.round(sec.completeness * 100)
  const isOverdue = sec.days_since_update != null && sec.days_since_update > 30
  return (
    <div className="flex items-center gap-4 py-2 border-b last:border-0">
      <div className="w-6 text-xs text-muted-foreground font-mono">{sec.section_number}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">{sec.section_name}</span>
          {isOverdue && (
            <Clock className="h-3 w-3 text-yellow-500 shrink-0" />
          )}
        </div>
        {sec.missing_fields.length > 0 && (
          <p className="text-xs text-muted-foreground truncate">
            Missing: {sec.missing_fields.slice(0, 3).join(', ')}
            {sec.missing_fields.length > 3 && ` +${sec.missing_fields.length - 3} more`}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Progress value={pct} className="w-20 h-2" />
        <span className="text-xs w-8 text-right">{pct}%</span>
      </div>
    </div>
  )
}

function EventRow({
  event,
  onResolve,
  resolving,
}: {
  event: ComplianceEvent
  onResolve: (id: string) => void
  resolving: boolean
}) {
  return (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      {event.status === 'open' ? (
        <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5 shrink-0" />
      ) : (
        <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm">
          {(event.details as Record<string, string>)?.message ?? 'Rule violated'}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {formatDate(event.triggered_at)}
        </p>
      </div>
      {event.status === 'open' && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => onResolve(event.id)}
          disabled={resolving}
        >
          Resolve
        </Button>
      )}
    </div>
  )
}

export default function CompliancePage() {
  const { id: systemId } = useParams<{ id: string }>()
  const { currentOrg } = useAuthStore()
  const qc = useQueryClient()
  const [ruleText, setRuleText] = useState('')
  const [generatedRule, setGeneratedRule] = useState<GeneratedRule | null>(null)
  const [showRuleGenerator, setShowRuleGenerator] = useState(false)

  const { data: health, isLoading } = useQuery({
    queryKey: ['compliance-health', systemId],
    queryFn: () => policyApi.health(systemId).then((r) => r.data),
  })

  const runChecksMutation = useMutation({
    mutationFn: () => policyApi.runChecks(systemId),
    onSuccess: (res) => {
      const d = res.data
      qc.invalidateQueries({ queryKey: ['compliance-health', systemId] })
      toast({
        title: 'Checks complete',
        description: `${d.evaluated} rules evaluated — ${d.violations} violation(s) found.`,
      })
    },
    onError: () => toast({ variant: 'destructive', title: 'Check run failed' }),
  })

  const resolveMutation = useMutation({
    mutationFn: (eventId: string) => policyApi.resolveEvent(systemId, eventId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['compliance-health', systemId] })
      toast({ title: 'Event resolved' })
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to resolve event' }),
  })

  const generateRuleMutation = useMutation({
    mutationFn: (description: string) =>
      ruleGeneratorApi.generateRule(currentOrg!.id, description).then((r) => r.data),
    onSuccess: (data) => {
      setGeneratedRule(data)
      toast({ title: 'Rule generated', description: data.suggested_name })
    },
    onError: () =>
      toast({ variant: 'destructive', title: 'Rule generation failed. Check OPENAI_API_KEY.' }),
  })

  const saveRuleMutation = useMutation({
    mutationFn: (rule: GeneratedRule) =>
      policyApi.createRule(currentOrg!.id, {
        name: rule.suggested_name,
        description: rule.description,
        condition: rule.condition,
        severity: 'warning',
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['compliance-health', systemId] })
      setGeneratedRule(null)
      setRuleText('')
      setShowRuleGenerator(false)
      toast({ title: 'Policy rule saved' })
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to save rule' }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!health) return null

  const overallPct = Math.round(health.overall_completeness * 100)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Compliance Health</h2>
          <p className="text-muted-foreground">
            Real-time compliance monitoring for{' '}
            <span className="font-medium">{health.system_name}</span>
          </p>
        </div>
        <Button
          onClick={() => runChecksMutation.mutate()}
          disabled={runChecksMutation.isPending}
        >
          <Play className="h-4 w-4 mr-2" />
          {runChecksMutation.isPending ? 'Running…' : 'Run Checks'}
        </Button>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-1">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Completeness</span>
            </div>
            <p className="text-3xl font-bold">{overallPct}%</p>
            <HealthScoreBadge score={health.overall_completeness} />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-1">
              {health.open_violations === 0 ? (
                <ShieldCheck className="h-4 w-4 text-green-500" />
              ) : (
                <ShieldAlert className="h-4 w-4 text-destructive" />
              )}
              <span className="text-xs text-muted-foreground">Open Violations</span>
            </div>
            <p className="text-3xl font-bold">{health.open_violations}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Days Since Revision</span>
            </div>
            <p className="text-3xl font-bold">
              {health.days_since_last_revision ?? '—'}
            </p>
            {health.days_since_last_revision != null && health.days_since_last_revision > 30 && (
              <Badge variant="destructive" className="text-xs">Overdue</Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-1">
              <FileSearch className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Missing Evidence</span>
            </div>
            <p className="text-3xl font-bold">{health.missing_evidence_count}</p>
            {health.unlinked_deployments > 0 && (
              <p className="text-xs text-yellow-600">
                +{health.unlinked_deployments} unlinked deploys
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Section debt */}
      <Card>
        <CardHeader>
          <CardTitle>Section Completeness</CardTitle>
          <CardDescription>
            Per-section documentation progress and staleness indicators
          </CardDescription>
        </CardHeader>
        <CardContent>
          {health.section_debt.length === 0 ? (
            <p className="text-sm text-muted-foreground">No revision found yet.</p>
          ) : (
            health.section_debt.map((sec) => (
              <SectionDebtRow key={sec.section_number} sec={sec} />
            ))
          )}
        </CardContent>
      </Card>

      {/* Open violations */}
      <Card>
        <CardHeader>
          <CardTitle>Open Violations</CardTitle>
          <CardDescription>Active compliance events requiring attention</CardDescription>
        </CardHeader>
        <CardContent>
          {health.open_events.length === 0 ? (
            <div className="flex items-center gap-2 text-green-600 text-sm py-2">
              <CheckCircle2 className="h-4 w-4" />
              No open violations — all checks passing.
            </div>
          ) : (
            health.open_events.map((event) => (
              <EventRow
                key={event.id}
                event={event}
                onResolve={(id) => resolveMutation.mutate(id)}
                resolving={resolveMutation.isPending}
              />
            ))
          )}
        </CardContent>
      </Card>

      {/* LLM Rule Generator (T4.4) */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Wand2 className="h-4 w-4" />
                Generate Policy Rule from Text
              </CardTitle>
              <CardDescription>
                Describe a compliance rule in natural language — AI will create it for you.
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowRuleGenerator(!showRuleGenerator)
                setGeneratedRule(null)
              }}
            >
              {showRuleGenerator ? 'Hide' : 'Use AI Generator'}
            </Button>
          </div>
        </CardHeader>
        {showRuleGenerator && (
          <CardContent className="space-y-4">
            <Textarea
              rows={3}
              placeholder="e.g. The Technical File must be updated every 14 days."
              value={ruleText}
              onChange={(e) => setRuleText(e.target.value)}
            />
            <Button
              size="sm"
              onClick={() => generateRuleMutation.mutate(ruleText)}
              disabled={!ruleText.trim() || generateRuleMutation.isPending || !currentOrg}
            >
              {generateRuleMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating…
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4 mr-2" />
                  Generate rule
                </>
              )}
            </Button>

            {generatedRule && (
              <div className="border rounded-md p-4 space-y-3 bg-muted/30">
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                    Suggested name
                  </p>
                  <p className="text-sm font-medium">{generatedRule.suggested_name}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                    Condition
                  </p>
                  <pre className="text-xs bg-background rounded border p-2 overflow-auto">
                    {JSON.stringify(generatedRule.condition, null, 2)}
                  </pre>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => saveRuleMutation.mutate(generatedRule)}
                    disabled={saveRuleMutation.isPending}
                  >
                    {saveRuleMutation.isPending ? 'Saving…' : 'Save rule'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setGeneratedRule(null)}
                  >
                    Discard
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Links to sub-features */}
      <div className="flex gap-3">
        <Link href={`/systems/${systemId}/compliance/shadow`}>
          <Button variant="outline" size="sm">
            Shadow Validation
          </Button>
        </Link>
        <Link href={`/systems/${systemId}/compliance/bias`}>
          <Button variant="outline" size="sm">
            Bias Audit
          </Button>
        </Link>
        <Link href={`/systems/${systemId}/iso42001`}>
          <Button variant="outline" size="sm">
            ISO 42001 Crosswalk
          </Button>
        </Link>
      </div>
    </div>
  )
}
