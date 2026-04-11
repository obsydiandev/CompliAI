'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { GitCompare, Loader2, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from '@/components/ui/use-toast'
import { useAuthStore } from '@/lib/auth'
import { cn } from '@/lib/utils'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Revision {
  id: string
  version: number
  created_at: string
  sections: Record<number, string>
}

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged'
  value: string
}

function computeLineDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n')
  const newLines = newText.split('\n')
  const result: DiffLine[] = []

  // Simple LCS-based diff
  const m = oldLines.length
  const n = newLines.length
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0))

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldLines[i - 1] === newLines[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  // Backtrack
  let i = m, j = n
  const ops: DiffLine[] = []
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      ops.push({ type: 'unchanged', value: oldLines[i - 1] })
      i--; j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      ops.push({ type: 'added', value: newLines[j - 1] })
      j--
    } else {
      ops.push({ type: 'removed', value: oldLines[i - 1] })
      i--
    }
  }

  return ops.reverse()
}

const SECTION_NAMES: Record<number, string> = {
  1: 'General Description',
  2: 'System Architecture',
  3: 'Training Data',
  4: 'Validation & Testing',
  5: 'Human Oversight',
  6: 'Risk Management',
  7: 'Post-Market Monitoring',
  8: 'Standards',
  9: 'Declaration of Conformity',
}

export default function RevisionDiffPage() {
  const params = useParams()
  const systemId = params.id as string
  const token = useAuthStore(s => s.token)

  const [revisions, setRevisions] = useState<Revision[]>([])
  const [baseRevId, setBaseRevId] = useState<string>('')
  const [compareRevId, setCompareRevId] = useState<string>('')
  const [selectedSection, setSelectedSection] = useState<number>(1)
  const [diff, setDiff] = useState<DiffLine[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [mode, setMode] = useState<'unified' | 'split'>('unified')

  const authHeaders = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    loadRevisions()
  }, [systemId])

  useEffect(() => {
    if (baseRevId && compareRevId) computeDiff()
  }, [baseRevId, compareRevId, selectedSection])

  const loadRevisions = async () => {
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/systems/${systemId}/technical-file`,
        { headers: authHeaders }
      )
      if (!res.ok) throw new Error('Failed to load')
      const data = await res.json()
      const revs: Revision[] = data.revisions || []
      setRevisions(revs)
      if (revs.length >= 2) {
        setBaseRevId(revs[revs.length - 2].id)
        setCompareRevId(revs[revs.length - 1].id)
      } else if (revs.length === 1) {
        setBaseRevId(revs[0].id)
        setCompareRevId(revs[0].id)
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to load revisions.', variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }

  const loadSections = async (revisionId: string): Promise<Record<number, string>> => {
    const res = await fetch(
      `${API_BASE}/api/v1/systems/${systemId}/technical-file/revisions/${revisionId}/sections`,
      { headers: authHeaders }
    )
    if (!res.ok) return {}
    const data = await res.json()
    const sections: Record<number, string> = {}
    for (const s of data.sections || []) {
      const text = Object.values(s.content || {}).filter(v => v).join('\n') as string
      sections[s.section_number] = text
    }
    return sections
  }

  const computeDiff = async () => {
    if (!baseRevId || !compareRevId) return
    setIsLoading(true)
    try {
      const [baseSecs, compareSecs] = await Promise.all([
        loadSections(baseRevId),
        loadSections(compareRevId),
      ])
      const baseText = baseSecs[selectedSection] || ''
      const compareText = compareSecs[selectedSection] || ''
      setDiff(computeLineDiff(baseText, compareText))
    } catch {
      toast({ title: 'Error', description: 'Failed to compute diff.', variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }

  const hasChanges = diff.some(l => l.type !== 'unchanged')
  const added = diff.filter(l => l.type === 'added').length
  const removed = diff.filter(l => l.type === 'removed').length

  if (revisions.length === 0 && !isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <GitCompare className="w-12 h-12 mx-auto mb-4 text-slate-300" />
        <h1 className="text-xl font-bold text-slate-700">No revisions to compare</h1>
        <p className="text-slate-500 mt-2">Create at least two revisions to use the diff viewer.</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <GitCompare className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold text-slate-900">Revision Diff Viewer</h1>
      </div>

      {/* Controls */}
      <Card className="mb-6">
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Base revision</label>
              <Select value={baseRevId} onValueChange={setBaseRevId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select base" />
                </SelectTrigger>
                <SelectContent>
                  {revisions.map(r => (
                    <SelectItem key={r.id} value={r.id}>
                      v{r.version} — {new Date(r.created_at).toLocaleDateString('en-GB')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Compare with</label>
              <Select value={compareRevId} onValueChange={setCompareRevId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select compare" />
                </SelectTrigger>
                <SelectContent>
                  {revisions.map(r => (
                    <SelectItem key={r.id} value={r.id}>
                      v{r.version} — {new Date(r.created_at).toLocaleDateString('en-GB')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Section</label>
              <Select value={String(selectedSection)} onValueChange={v => setSelectedSection(Number(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(SECTION_NAMES).map(([num, name]) => (
                    <SelectItem key={num} value={num}>§{num} — {name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <Button
                variant={mode === 'unified' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMode('unified')}
              >
                Unified
              </Button>
              <Button
                variant={mode === 'split' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMode('split')}
              >
                Split
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      {!isLoading && (
        <div className="flex items-center gap-4 mb-4 text-sm">
          <span className="text-slate-500">
            §{selectedSection}: {SECTION_NAMES[selectedSection]}
          </span>
          {hasChanges ? (
            <>
              <span className="text-green-700 bg-green-100 px-2 py-0.5 rounded">+{added} lines</span>
              <span className="text-red-700 bg-red-100 px-2 py-0.5 rounded">-{removed} lines</span>
            </>
          ) : (
            <span className="text-slate-400">No changes in this section</span>
          )}
        </div>
      )}

      {/* Diff display */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          ) : diff.length === 0 ? (
            <div className="py-12 text-center text-slate-400">
              <p>No content in this section for the selected revisions.</p>
            </div>
          ) : mode === 'unified' ? (
            <div className="font-mono text-sm overflow-x-auto">
              {diff.map((line, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex px-4 py-0.5 border-l-4',
                    line.type === 'added' && 'bg-green-50 border-green-500',
                    line.type === 'removed' && 'bg-red-50 border-red-500 line-through',
                    line.type === 'unchanged' && 'border-transparent text-slate-500'
                  )}
                >
                  <span className={cn(
                    'w-4 mr-4 select-none',
                    line.type === 'added' && 'text-green-600',
                    line.type === 'removed' && 'text-red-600',
                    line.type === 'unchanged' && 'text-slate-300'
                  )}>
                    {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
                  </span>
                  <span className="whitespace-pre-wrap break-all">{line.value || ' '}</span>
                </div>
              ))}
            </div>
          ) : (
            // Split view
            <div className="grid grid-cols-2 divide-x font-mono text-xs overflow-x-auto">
              <div>
                <div className="px-3 py-2 bg-slate-50 border-b text-xs text-slate-500 font-sans">
                  Base (v{revisions.find(r => r.id === baseRevId)?.version || '?'})
                </div>
                {diff
                  .filter(l => l.type !== 'added')
                  .map((line, i) => (
                    <div
                      key={i}
                      className={cn(
                        'px-3 py-0.5',
                        line.type === 'removed' && 'bg-red-50 text-red-800'
                      )}
                    >
                      <span className="whitespace-pre-wrap break-all">{line.value || ' '}</span>
                    </div>
                  ))}
              </div>
              <div>
                <div className="px-3 py-2 bg-slate-50 border-b text-xs text-slate-500 font-sans">
                  Compare (v{revisions.find(r => r.id === compareRevId)?.version || '?'})
                </div>
                {diff
                  .filter(l => l.type !== 'removed')
                  .map((line, i) => (
                    <div
                      key={i}
                      className={cn(
                        'px-3 py-0.5',
                        line.type === 'added' && 'bg-green-50 text-green-800'
                      )}
                    >
                      <span className="whitespace-pre-wrap break-all">{line.value || ' '}</span>
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
