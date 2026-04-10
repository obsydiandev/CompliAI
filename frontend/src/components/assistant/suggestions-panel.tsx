'use client'

import { useState } from 'react'
import { Sparkles, Loader2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { assistantApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/use-toast'
import type { SuggestionsResult } from '@/types'

interface SuggestionsPanelProps {
  systemId: string
  sectionNumber: number
  /** Known missing fields (from completeness check). Used for badge count. */
  missingFields?: string[]
}

export function SuggestionsPanel({
  systemId,
  sectionNumber,
  missingFields = [],
}: SuggestionsPanelProps) {
  const [suggestions, setSuggestions] = useState<Record<string, string> | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  const { mutate, isPending } = useMutation({
    mutationFn: () =>
      assistantApi.getSuggestions(systemId, sectionNumber).then((r) => r.data),
    onSuccess: (data: SuggestionsResult) => {
      setSuggestions(data.suggestions)
      setIsOpen(true)
    },
    onError: () =>
      toast({ variant: 'destructive', title: 'Could not fetch suggestions' }),
  })

  const hasSuggestions = suggestions && Object.keys(suggestions).length > 0
  const missingCount = missingFields.length

  if (missingCount === 0) return null

  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20 p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
          <span className="text-sm font-medium text-amber-800 dark:text-amber-400">
            {missingCount} required field{missingCount !== 1 ? 's' : ''} missing
          </span>
          {hasSuggestions && (
            <Badge
              variant="outline"
              className="text-xs text-amber-700 border-amber-400 bg-amber-100"
            >
              AI hints available
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!hasSuggestions && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-7 text-xs gap-1 border-amber-400 text-amber-700 hover:bg-amber-100"
              onClick={() => mutate()}
              disabled={isPending}
            >
              {isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Sparkles className="h-3 w-3" />
              )}
              Get AI hints
            </Button>
          )}
          {hasSuggestions && (
            <button
              type="button"
              onClick={() => setIsOpen((v) => !v)}
              className="text-xs text-amber-700 hover:text-amber-900 flex items-center gap-0.5"
            >
              {isOpen ? (
                <>
                  <ChevronUp className="h-3 w-3" />Hide
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" />Show hints
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {isOpen && hasSuggestions && (
        <div className="space-y-2 pt-1 border-t border-amber-200 dark:border-amber-800">
          {Object.entries(suggestions!).map(([field, hint]) => (
            <div key={field} className="space-y-0.5">
              <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
                {field.replace(/_/g, ' ')}
              </span>
              <p className="text-xs text-amber-800 dark:text-amber-300">{hint}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
