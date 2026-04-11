'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  GitCompare,
  Clock,
  ChevronDown,
  ChevronRight,
  Plus,
  Minus,
  AlertCircle,
} from 'lucide-react'
import { tfApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from '@/components/ui/use-toast'
import type { TechnicalFileRevision, RevisionDiff } from '@/types'

const SECTION_NAMES: Record<number, string> = {
  1: 'General Description',
  2: 'System Architecture & Technical Specifications',
  3: 'Training Data',
  4: 'Validation & Testing',
  5: 'Risk Management',
  6: 'Conformity Assessment',
  7: 'Human Oversight',
  8: 'Accuracy & Robustness',
  9: 'Post-Market Monitoring',
}

function ValueDisplay({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground italic">—</span>
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-muted-foreground italic">[]</span>
    return (
      <ul className="list-disc list-inside space-y-0.5">
        {value.map((item, i) => (
          <li key={i} className="text-sm">
            {String(item)}
          </li>
        ))}
      </ul>
    )
  }
  if (typeof value === 'object') {
    return (
      <pre className="text-xs bg-muted rounded p-1 overflow-auto max-h-32 whitespace-pre-wrap">
        {JSON.stringify(value, null, 2)}
      </pre>
    )
  }
  return <span className="text-sm break-words">{String(value)}</span>
}

function SectionDiffCard({ diff }: { diff: RevisionDiff }) {
  const [expanded, setExpanded] = useState(true)
  const sectionName = SECTION_NAMES[diff.section_number] ?? `Section ${diff.section_number}`

  return (
    <Card>
      <CardHeader className="pb-2 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {expanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            <CardTitle className="text-base">
              Section {diff.section_number}: {sectionName}
            </CardTitle>
          </div>
          <Badge variant="secondary">
            {diff.changed_fields.length} field{diff.changed_fields.length !== 1 ? 's' : ''} changed
          </Badge>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent>
          <div className="space-y-4">
            {diff.changed_fields.map((field) => (
              <div key={field} className="border rounded-md overflow-hidden">
                <div className="bg-muted px-3 py-1.5 border-b">
                  <span className="text-xs font-mono font-medium">{field}</span>
                </div>
                <div className="grid grid-cols-2 divide-x">
                  <div className="p-3 bg-red-50 dark:bg-red-950/20">
                    <div className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400 font-medium mb-1">
                      <Minus className="h-3 w-3" />
                      Before
                    </div>
                    <ValueDisplay value={diff.old_values[field]} />
                  </div>
                  <div className="p-3 bg-green-50 dark:bg-green-950/20">
                    <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium mb-1">
                      <Plus className="h-3 w-3" />
                      After
                    </div>
                    <ValueDisplay value={diff.new_values[field]} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  )
}

function RevisionOption({ rev }: { rev: TechnicalFileRevision }) {
  return (
    <SelectItem value={rev.id}>
      <span className="flex items-center gap-2">
        <span className="font-mono text-sm">v{rev.version}</span>
        <span className="text-muted-foreground text-xs">{formatDate(rev.created_at)}</span>
        <Badge
          variant={
            rev.status === 'approved' ? 'default' : rev.status === 'archived' ? 'secondary' : 'outline'
          }
          className="text-xs"
        >
          {rev.status}
        </Badge>
      </span>
    </SelectItem>
  )
}

export default function RevisionsPage() {
  const { id } = useParams<{ id: string }>()
  const [baseRevId, setBaseRevId] = useState<string>('')
  const [compareRevId, setCompareRevId] = useState<string>('')

  const { data: revisions, isLoading: revsLoading } = useQuery({
    queryKey: ['revisions', id],
    queryFn: () => tfApi.listRevisions(id).then((r) => r.data),
  })

  // Auto-select latest two revisions once data loads
  useEffect(() => {
    if (revisions && revisions.length >= 2 && !baseRevId) {
      setBaseRevId(revisions[1].id)
      setCompareRevId(revisions[0].id)
    }
  }, [revisions]) // eslint-disable-line react-hooks/exhaustive-deps

  const canDiff = !!(baseRevId && compareRevId && baseRevId !== compareRevId)

  const {
    data: diffData,
    isLoading: diffLoading,
    error: diffError,
  } = useQuery({
    queryKey: ['revision-diff', id, baseRevId, compareRevId],
    queryFn: () => tfApi.diffRevisions(id, baseRevId, compareRevId).then((r) => r.data),
    enabled: canDiff,
    retry: false,
  })

  if (revsLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-muted rounded w-48" />
        <div className="h-32 bg-muted rounded" />
      </div>
    )
  }

  if (!revisions || revisions.length === 0) {
    return (
      <div className="space-y-4">
        <Link href={`/systems/${id}`} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to system
        </Link>
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            <GitCompare className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No revisions yet. Create at least two revisions to compare them.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (revisions.length < 2) {
    return (
      <div className="space-y-4">
        <Link href={`/systems/${id}`} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to system
        </Link>
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            <GitCompare className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>At least two revisions are needed to compare. Currently only 1 revision exists.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

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

      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <GitCompare className="h-6 w-6" />
          Revision Diff Viewer
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Compare changes between two revisions of the Technical File.
        </p>
      </div>

      {/* Revision selectors */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Select Revisions to Compare</CardTitle>
          <CardDescription>Choose a base (before) and a target (after) revision.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1 space-y-1">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Base (before)
              </label>
              <Select value={baseRevId} onValueChange={setBaseRevId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select base revision…" />
                </SelectTrigger>
                <SelectContent>
                  {revisions.map((rev) => (
                    <RevisionOption key={rev.id} rev={rev} />
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="mt-5">
              <GitCompare className="h-5 w-5 text-muted-foreground" />
            </div>

            <div className="flex-1 space-y-1">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Compare (after)
              </label>
              <Select value={compareRevId} onValueChange={setCompareRevId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select compare revision…" />
                </SelectTrigger>
                <SelectContent>
                  {revisions.map((rev) => (
                    <RevisionOption key={rev.id} rev={rev} />
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {baseRevId === compareRevId && baseRevId && (
            <p className="text-sm text-yellow-600 mt-2 flex items-center gap-1">
              <AlertCircle className="h-4 w-4" />
              Please select two different revisions to compare.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Diff results */}
      {diffLoading && (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-muted rounded-lg" />
          ))}
        </div>
      )}

      {diffError && (
        <Card className="border-destructive">
          <CardContent className="pt-4 text-destructive flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            Failed to load diff. Please try again.
          </CardContent>
        </Card>
      )}

      {diffData && !diffLoading && (
        <>
          {diffData.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                <p>No differences found between the selected revisions.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {diffData.length} section{diffData.length !== 1 ? 's' : ''} with changes
                </p>
              </div>
              {diffData.map((diff) => (
                <SectionDiffCard key={diff.section_number} diff={diff} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
