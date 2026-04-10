'use client'

import { useParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Sparkles } from 'lucide-react'
import { tfApi, sectionApi, evidenceApi } from '@/lib/api'
import { ANNEX_IV_SECTION_METADATA } from '@/lib/annex-iv-metadata'
import { formatPercent } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/use-toast'
import { EvidenceList } from '@/components/evidence/evidence-list'
import { EvidenceUpload } from '@/components/evidence/evidence-upload'

export default function SectionEditorPage() {
  const { id, sectionNumber } = useParams<{ id: string; sectionNumber: string }>()
  const sectionNum = parseInt(sectionNumber, 10)
  const qc = useQueryClient()

  const sectionMeta = ANNEX_IV_SECTION_METADATA.find((s) => s.number === sectionNum)

  const { data: revisions } = useQuery({
    queryKey: ['revisions', id],
    queryFn: () => tfApi.listRevisions(id).then((r) => r.data),
  })
  const currentRevision = revisions?.[0]

  const { data: section, isLoading } = useQuery({
    queryKey: ['section', id, currentRevision?.id, sectionNum],
    queryFn: () =>
      sectionApi.get(id, currentRevision!.id, sectionNum).then((r) => r.data),
    enabled: !!currentRevision,
  })

  const { data: evidence } = useQuery({
    queryKey: ['evidence', currentRevision?.id],
    queryFn: () => evidenceApi.list(currentRevision!.id).then((r) => r.data),
    enabled: !!currentRevision,
  })

  const { register, handleSubmit } = useForm<Record<string, string>>({
    values: section
      ? Object.fromEntries(
          Object.entries(section.content).map(([k, v]) => [
            k,
            Array.isArray(v) ? JSON.stringify(v, null, 2) : String(v ?? ''),
          ])
        )
      : {},
  })

  const saveMutation = useMutation({
    mutationFn: (formValues: Record<string, string>) => {
      const content: Record<string, unknown> = {}
      sectionMeta?.fields.forEach((field) => {
        const raw = formValues[field.key] ?? ''
        if (field.type === 'array') {
          try {
            content[field.key] = JSON.parse(raw)
          } catch {
            content[field.key] = raw.split('\n').filter(Boolean)
          }
        } else {
          content[field.key] = raw
        }
      })
      return sectionApi.update(id, currentRevision!.id, sectionNum, content)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['section', id, currentRevision?.id, sectionNum] })
      qc.invalidateQueries({ queryKey: ['completeness', id, currentRevision?.id] })
      toast({ title: 'Section saved' })
    },
    onError: () =>
      toast({ variant: 'destructive', title: 'Save failed' }),
  })

  const deleteEvidenceMutation = useMutation({
    mutationFn: (evidenceId: string) => evidenceApi.delete(evidenceId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['evidence', currentRevision?.id] })
      toast({ title: 'Evidence removed' })
    },
  })

  if (!sectionMeta) return <p>Section not found.</p>

  const score = section?.completeness_score ?? 0
  const sectionEvidence = (evidence ?? []).filter(
    (e) => e.section_id === section?.id || e.field_key?.startsWith(`${sectionNum}_`)
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <Badge variant="outline">§{sectionMeta.number}</Badge>
          <h2 className="text-xl font-semibold">{sectionMeta.name}</h2>
        </div>
        <p className="text-sm text-muted-foreground">{sectionMeta.description}</p>
      </div>

      {/* Completeness bar */}
      <div className="flex items-center gap-3">
        <Progress value={score * 100} className="h-2 flex-1" />
        <span className="text-sm font-medium w-12 text-right">{formatPercent(score)}</span>
      </div>

      {/* AI hint banner */}
      <div className="flex items-center gap-3 p-3 rounded-md border border-primary/30 bg-primary/5 text-sm text-primary">
        <Sparkles className="h-4 w-4 shrink-0" />
        <span>
          <strong>AI Copilot available</strong> — Generate a draft for this section using your
          system metadata. (Coming soon)
        </span>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Form */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Section Content</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4 animate-pulse">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="space-y-1">
                      <div className="h-3 bg-muted rounded w-32" />
                      <div className="h-20 bg-muted rounded" />
                    </div>
                  ))}
                </div>
              ) : (
                <form
                  onSubmit={handleSubmit((v) => saveMutation.mutate(v))}
                  className="space-y-5"
                >
                  {sectionMeta.fields.map((field) => (
                    <div key={field.key} className="space-y-1">
                      <label className="text-sm font-medium">
                        {field.label}
                        {field.required && (
                          <span className="ml-1 text-destructive">*</span>
                        )}
                      </label>
                      {field.type === 'text' ? (
                        <Input {...register(field.key)} />
                      ) : (
                        <Textarea
                          rows={field.type === 'array' ? 4 : 5}
                          placeholder={
                            field.type === 'array'
                              ? 'Enter as JSON array or one item per line'
                              : ''
                          }
                          {...register(field.key)}
                        />
                      )}
                      {field.help && (
                        <p className="text-xs text-muted-foreground">{field.help}</p>
                      )}
                    </div>
                  ))}

                  <Button type="submit" disabled={saveMutation.isPending || !currentRevision}>
                    {saveMutation.isPending ? 'Saving…' : 'Save section'}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Evidence panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Evidence</CardTitle>
              <CardDescription>Supporting documents for this section</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <EvidenceList
                evidence={sectionEvidence}
                onDelete={(evidenceId) => deleteEvidenceMutation.mutate(evidenceId)}
                onAdd={() => {}}
              />
              {currentRevision && section && (
                <EvidenceUpload
                  revisionId={currentRevision.id}
                  sectionId={section.id}
                  onUploaded={() =>
                    qc.invalidateQueries({ queryKey: ['evidence', currentRevision.id] })
                  }
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
