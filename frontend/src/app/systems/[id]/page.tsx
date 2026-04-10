'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Download, Plus, Clock, Settings } from 'lucide-react'
import { systemApi, tfApi, sectionApi, exportApi } from '@/lib/api'
import { formatDate, formatPercent, downloadBlob } from '@/lib/utils'
import { ANNEX_IV_SECTION_METADATA } from '@/lib/annex-iv-metadata'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { toast } from '@/components/ui/use-toast'
import type { AISystemCategory } from '@/types'

function categoryLabel(c: AISystemCategory) {
  if (c === 'high_risk') return 'High Risk'
  if (c === 'limited_risk') return 'Limited Risk'
  return 'Minimal Risk'
}

function categoryVariant(c: AISystemCategory) {
  if (c === 'high_risk') return 'destructive' as const
  if (c === 'limited_risk') return 'secondary' as const
  return 'outline' as const
}

export default function SystemDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()

  const { data: system, isLoading: sysLoading } = useQuery({
    queryKey: ['system', id],
    queryFn: () => systemApi.get(id).then((r) => r.data),
  })

  const { data: revisions } = useQuery({
    queryKey: ['revisions', id],
    queryFn: () => tfApi.listRevisions(id).then((r) => r.data),
  })

  const currentRevision = revisions?.[0]

  const { data: completeness } = useQuery({
    queryKey: ['completeness', id, currentRevision?.id],
    queryFn: () =>
      sectionApi.completeness(id, currentRevision!.id).then((r) => r.data),
    enabled: !!currentRevision,
  })

  const createRevMutation = useMutation({
    mutationFn: () => tfApi.createRevision(id, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['revisions', id] })
      toast({ title: 'New revision created' })
    },
    onError: () =>
      toast({ variant: 'destructive', title: 'Failed to create revision' }),
  })

  async function exportPDF() {
    if (!currentRevision) return
    try {
      const res = await exportApi.pdf(id, currentRevision.id)
      downloadBlob(res.data as Blob, `technical-file-${id}.pdf`)
    } catch {
      toast({ variant: 'destructive', title: 'Export failed' })
    }
  }

  async function exportMarkdown() {
    if (!currentRevision) return
    try {
      const res = await exportApi.markdown(id, currentRevision.id)
      const blob = new Blob([res.data as string], { type: 'text/markdown' })
      downloadBlob(blob, `technical-file-${id}.md`)
    } catch {
      toast({ variant: 'destructive', title: 'Export failed' })
    }
  }

  if (sysLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-muted rounded w-64" />
        <div className="h-4 bg-muted rounded w-48" />
      </div>
    )
  }

  if (!system) return <p>System not found.</p>

  const overall = completeness?.overall ?? 0
  const sectionScores = completeness?.sections ?? {}
  const missing = completeness?.missing_by_section ?? {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">{system.name}</h1>
            <Badge variant={categoryVariant(system.category)}>
              {categoryLabel(system.category)}
            </Badge>
            {system.annex_iii_classification && (
              <Badge variant="destructive">Annex III</Badge>
            )}
          </div>
          {system.description && (
            <p className="text-muted-foreground text-sm">{system.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={exportMarkdown} disabled={!currentRevision}>
            <Download className="h-4 w-4 mr-1" /> Markdown
          </Button>
          <Button variant="outline" size="sm" onClick={exportPDF} disabled={!currentRevision}>
            <FileText className="h-4 w-4 mr-1" /> PDF
          </Button>
          <Link href={`/systems/${id}/settings`}>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Nav tabs */}
      <div className="flex gap-1 border-b">
        {['Annex IV', 'Evidence', 'Settings'].map((tab) => {
          const href =
            tab === 'Annex IV'
              ? `/systems/${id}/annex-iv`
              : tab === 'Evidence'
              ? `/systems/${id}/evidence`
              : `/systems/${id}/settings`
          return (
            <Link
              key={tab}
              href={href}
              className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground border-b-2 border-transparent hover:border-primary transition-colors"
            >
              {tab}
            </Link>
          )
        })}
      </div>

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Section completeness */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Section Completeness — {formatPercent(overall)} overall
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {ANNEX_IV_SECTION_METADATA.map((sec) => {
              const score = sectionScores[sec.number.toString()] ?? 0
              const missingCount = missing[sec.number.toString()]?.length ?? 0
              return (
                <div key={sec.number} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>
                      §{sec.number} {sec.name}
                      {missingCount > 0 && (
                        <span className="ml-2 text-xs text-destructive">
                          ({missingCount} missing)
                        </span>
                      )}
                    </span>
                    <span className="text-muted-foreground">{formatPercent(score)}</span>
                  </div>
                  <Progress value={score * 100} className="h-1.5" />
                </div>
              )
            })}
          </CardContent>
        </Card>

        {/* Revision history */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Revision History</CardTitle>
              <Button
                size="sm"
                onClick={() => createRevMutation.mutate()}
                disabled={createRevMutation.isPending}
              >
                <Plus className="h-4 w-4 mr-1" />
                New Revision
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {!revisions || revisions.length === 0 ? (
              <p className="text-sm text-muted-foreground">No revisions yet.</p>
            ) : (
              <ol className="relative border-l border-muted ml-3 space-y-4">
                {revisions.map((rev) => (
                  <li key={rev.id} className="ml-4">
                    <div className="absolute -left-1.5 mt-1.5 h-3 w-3 rounded-full border bg-primary" />
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">v{rev.version}</span>
                      <Badge
                        variant={
                          rev.status === 'approved'
                            ? 'default'
                            : rev.status === 'archived'
                            ? 'secondary'
                            : 'outline'
                        }
                        className="text-xs"
                      >
                        {rev.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
                      <Clock className="h-3 w-3" />
                      {formatDate(rev.created_at)}
                    </div>
                    {rev.change_summary && (
                      <p className="text-xs text-muted-foreground mt-0.5">{rev.change_summary}</p>
                    )}
                    <Link
                      href={`/systems/${id}/annex-iv`}
                      className="text-xs text-primary hover:underline"
                    >
                      View sections →
                    </Link>
                  </li>
                ))}
              </ol>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
