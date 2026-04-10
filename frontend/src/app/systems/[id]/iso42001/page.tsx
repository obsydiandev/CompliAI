'use client'

import { useParams } from 'next/navigation'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { FileCheck2, Download, Loader2 } from 'lucide-react'
import { templateApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { toast } from '@/components/ui/use-toast'
import type { CrosswalkEntry, EvidencePackage } from '@/types'

function CoverageBadge({ coverage }: { coverage: string }) {
  if (coverage === 'full')
    return <Badge className="bg-green-100 text-green-800 border-green-200">Full</Badge>
  if (coverage === 'partial')
    return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Partial</Badge>
  return <Badge variant="outline">Supplementary</Badge>
}

function SectionPill({ num }: { num: number }) {
  return (
    <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary/10 text-primary text-xs font-medium">
      {num}
    </span>
  )
}

export default function ISO42001Page() {
  const { id: systemId } = useParams<{ id: string }>()
  const [showPackage, setShowPackage] = useState(false)

  const { data: crosswalk, isLoading } = useQuery({
    queryKey: ['iso42001-crosswalk', systemId],
    queryFn: () => templateApi.getCrosswalk(systemId).then((r) => r.data),
  })

  const packageMutation = useMutation({
    mutationFn: () => templateApi.getEvidencePackage(systemId),
    onSuccess: () => setShowPackage(true),
    onError: () => toast({ variant: 'destructive', title: 'Failed to generate package' }),
  })

  const pkg: EvidencePackage | undefined = packageMutation.data?.data

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">ISO 42001 Crosswalk</h2>
          <p className="text-muted-foreground">
            Mapping between Annex IV sections and ISO/IEC 42001:2023 controls
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => packageMutation.mutate()}
          disabled={packageMutation.isPending}
        >
          {packageMutation.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <FileCheck2 className="h-4 w-4 mr-2" />
          )}
          Generate Evidence Package
        </Button>
      </div>

      {/* Evidence package summary */}
      {showPackage && pkg && (
        <Card className="border-green-200 bg-green-50/50">
          <CardHeader>
            <CardTitle className="text-base">ISO 42001 Evidence Package</CardTitle>
            <CardDescription>
              Coverage based on completed Annex IV sections
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex justify-between text-sm mb-1">
                  <span>Coverage</span>
                  <span className="font-semibold">{pkg.coverage_pct}%</span>
                </div>
                <Progress value={pkg.coverage_pct} className="h-3" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-green-600">{pkg.fully_covered}</p>
                <p className="text-xs text-muted-foreground">Fully Covered</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-yellow-600">{pkg.partially_covered}</p>
                <p className="text-xs text-muted-foreground">Partially Covered</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-muted-foreground">{pkg.not_covered}</p>
                <p className="text-xs text-muted-foreground">Not Covered</p>
              </div>
            </div>
            {pkg.not_covered_clauses.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Uncovered controls:</p>
                <div className="flex flex-wrap gap-1">
                  {pkg.not_covered_clauses.map((c) => (
                    <Badge key={c} variant="outline" className="text-xs">
                      {c}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Crosswalk table */}
      <Card>
        <CardHeader>
          <CardTitle>Control Mapping</CardTitle>
          <CardDescription>
            {crosswalk?.length ?? 0} ISO 42001 controls mapped to Annex IV sections
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="px-4 py-3 text-left font-medium w-24">Clause</th>
                  <th className="px-4 py-3 text-left font-medium">Title</th>
                  <th className="px-4 py-3 text-left font-medium w-32">Annex IV</th>
                  <th className="px-4 py-3 text-left font-medium w-28">Coverage</th>
                  <th className="px-4 py-3 text-left font-medium">Notes</th>
                </tr>
              </thead>
              <tbody>
                {(crosswalk ?? []).map((entry: CrosswalkEntry) => (
                  <tr key={entry.iso_clause} className="border-b hover:bg-muted/20">
                    <td className="px-4 py-3 font-mono text-xs">{entry.iso_clause}</td>
                    <td className="px-4 py-3 font-medium">{entry.iso_title}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {entry.annex_iv_sections.map((n) => (
                          <SectionPill key={n} num={n} />
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <CoverageBadge coverage={entry.coverage} />
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground max-w-xs">
                      {entry.notes}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
