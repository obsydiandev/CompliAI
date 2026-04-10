'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { tfApi, sectionApi } from '@/lib/api'
import { ANNEX_IV_SECTION_METADATA } from '@/lib/annex-iv-metadata'
import { formatPercent } from '@/lib/utils'
import { SectionCard } from '@/components/annex-iv/section-card'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function AnnexIVPage() {
  const { id } = useParams<{ id: string }>()

  const { data: revisions } = useQuery({
    queryKey: ['revisions', id],
    queryFn: () => tfApi.listRevisions(id).then((r) => r.data),
  })

  const currentRevision = revisions?.[0]

  const { data: completeness, isLoading } = useQuery({
    queryKey: ['completeness', id, currentRevision?.id],
    queryFn: () =>
      sectionApi.completeness(id, currentRevision!.id).then((r) => r.data),
    enabled: !!currentRevision,
  })

  const overall = completeness?.overall ?? 0
  const sectionScores = completeness?.sections ?? {}
  const missing = completeness?.missing_by_section ?? {}

  if (!currentRevision && !isLoading) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Annex IV Technical File</h2>
        <p className="text-muted-foreground text-sm">
          No revision exists yet. Go to the system page and create a revision first.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">Annex IV Technical File</h2>
        {currentRevision && (
          <p className="text-sm text-muted-foreground">
            Current revision: <span className="font-medium">v{currentRevision.version}</span>
            {' · '}
            <span
              className={
                currentRevision.status === 'approved'
                  ? 'text-green-600'
                  : 'text-muted-foreground'
              }
            >
              {currentRevision.status}
            </span>
          </p>
        )}
      </div>

      {/* Overall completeness */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Overall Completeness
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-3xl font-bold">{formatPercent(overall)}</span>
            <span className="text-sm text-muted-foreground">
              {Object.values(missing).flat().length} fields missing
            </span>
          </div>
          <Progress value={overall * 100} className="h-3" />
        </CardContent>
      </Card>

      {/* Section cards grid */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {ANNEX_IV_SECTION_METADATA.map((sec) => {
          const score = sectionScores[sec.number.toString()] ?? 0
          const missingFields = missing[sec.number.toString()] ?? []
          return (
            <SectionCard
              key={sec.number}
              sectionNumber={sec.number}
              sectionName={sec.name}
              completenessScore={score}
              missingFields={missingFields}
              onEdit={() =>
                window.location.assign(`/systems/${id}/annex-iv/sections/${sec.number}`)
              }
            />
          )
        })}
      </div>
    </div>
  )
}
