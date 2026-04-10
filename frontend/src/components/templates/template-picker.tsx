'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ChevronRight, FileText, Loader2, CheckCircle2 } from 'lucide-react'
import { templateApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { toast } from '@/components/ui/use-toast'
import type { TemplateSummary } from '@/types'

interface Props {
  systemId: string
  revisionId: string
  onApplied?: () => void
}

export function TemplatePicker({ systemId, revisionId, onApplied }: Props) {
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [overwrite, setOverwrite] = useState(false)

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => templateApi.list().then((r) => r.data),
    enabled: open,
  })

  const applyMutation = useMutation({
    mutationFn: () =>
      templateApi.apply(systemId, selected!, revisionId, overwrite),
    onSuccess: (res) => {
      const d = res.data as { applied_sections: number[]; skipped_sections: number[] }
      toast({
        title: 'Template applied',
        description: `${d.applied_sections.length} section(s) updated.`,
      })
      setOpen(false)
      setSelected(null)
      onApplied?.()
    },
    onError: () =>
      toast({ variant: 'destructive', title: 'Failed to apply template' }),
  })

  const selectedTemplate = templates.find((t: TemplateSummary) => t.id === selected)

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <FileText className="h-4 w-4 mr-2" />
          Use Template
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Template Library</DialogTitle>
          <DialogDescription>
            Select a pre-filled template to jumpstart your Annex IV documentation.
            Templates fill empty fields only by default.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {templates.map((tpl: TemplateSummary) => (
              <button
                key={tpl.id}
                type="button"
                onClick={() => setSelected(tpl.id === selected ? null : tpl.id)}
                className={`w-full text-left rounded-lg border p-4 transition-colors ${
                  selected === tpl.id
                    ? 'border-primary bg-primary/5'
                    : 'hover:border-primary/40 hover:bg-muted/30'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{tpl.name}</span>
                      {selected === tpl.id && (
                        <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {tpl.description}
                    </p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {tpl.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs py-0">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground shrink-0">
                    {tpl.sections_count} sections
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {selected && selectedTemplate && (
          <div className="rounded-lg border bg-muted/30 p-3 text-sm">
            <p className="font-medium mb-1">{selectedTemplate.name} — selected</p>
            <div className="flex items-center gap-2 mt-3">
              <input
                id="overwrite"
                type="checkbox"
                checked={overwrite}
                onChange={(e) => setOverwrite(e.target.checked)}
                className="h-4 w-4 rounded border-input"
              />
              <label htmlFor="overwrite" className="text-xs cursor-pointer">
                Overwrite existing content
              </label>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => applyMutation.mutate()}
            disabled={!selected || applyMutation.isPending}
          >
            {applyMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Applying…
              </>
            ) : (
              <>
                Apply Template
                <ChevronRight className="h-4 w-4 ml-1" />
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

