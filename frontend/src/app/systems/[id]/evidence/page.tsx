'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { tfApi, evidenceApi } from '@/lib/api'
import { ANNEX_IV_SECTION_METADATA } from '@/lib/annex-iv-metadata'
import { EvidenceList } from '@/components/evidence/evidence-list'
import { EvidenceUpload } from '@/components/evidence/evidence-upload'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/use-toast'

export default function EvidencePage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [filterSection, setFilterSection] = useState<string>('all')

  const { data: revisions } = useQuery({
    queryKey: ['revisions', id],
    queryFn: () => tfApi.listRevisions(id).then((r) => r.data),
  })
  const currentRevision = revisions?.[0]

  const { data: evidence, isLoading } = useQuery({
    queryKey: ['evidence', currentRevision?.id],
    queryFn: () => evidenceApi.list(currentRevision!.id).then((r) => r.data),
    enabled: !!currentRevision,
  })

  const deleteMutation = useMutation({
    mutationFn: (evidenceId: string) => evidenceApi.delete(evidenceId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['evidence', currentRevision?.id] })
      toast({ title: 'Evidence removed' })
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to remove evidence' }),
  })

  const filteredEvidence =
    filterSection === 'all'
      ? (evidence ?? [])
      : (evidence ?? []).filter((e) =>
          e.field_key?.startsWith(`${filterSection}_`)
        )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Evidence</h2>
        <p className="text-muted-foreground text-sm">
          Supporting documents and links for this Technical File revision.
        </p>
      </div>

      {/* Section filter */}
      <div className="flex flex-wrap gap-2">
        <Badge
          variant={filterSection === 'all' ? 'default' : 'outline'}
          className="cursor-pointer"
          onClick={() => setFilterSection('all')}
        >
          All
        </Badge>
        {ANNEX_IV_SECTION_METADATA.map((sec) => (
          <Badge
            key={sec.number}
            variant={filterSection === sec.number.toString() ? 'default' : 'outline'}
            className="cursor-pointer"
            onClick={() => setFilterSection(sec.number.toString())}
          >
            §{sec.number}
          </Badge>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {filteredEvidence.length} evidence item
                {filteredEvidence.length !== 1 ? 's' : ''}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2 animate-pulse">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-12 bg-muted rounded" />
                  ))}
                </div>
              ) : (
                <EvidenceList
                  evidence={filteredEvidence}
                  onDelete={(evidenceId) => deleteMutation.mutate(evidenceId)}
                  onAdd={() => {}}
                />
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Upload Evidence</CardTitle>
            </CardHeader>
            <CardContent>
              {currentRevision ? (
                <EvidenceUpload
                  revisionId={currentRevision.id}
                  onUploaded={() =>
                    qc.invalidateQueries({ queryKey: ['evidence', currentRevision.id] })
                  }
                />
              ) : (
                <p className="text-sm text-muted-foreground">No active revision.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
