import Link from 'next/link'
import { ArrowRight, ShieldAlert } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CompletenessBar } from '@/components/annex-iv/completeness-bar'
import { formatDate } from '@/lib/utils'
import type { AISystem, AISystemCategory } from '@/types'

interface SystemCardProps {
  system: AISystem
}

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

export function SystemCard({ system }: SystemCardProps) {
  return (
    <Card className="flex flex-col">
      <CardContent className="flex-1 pt-5 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold leading-tight">{system.name}</h3>
          <div className="flex flex-col gap-1 items-end shrink-0">
            <Badge variant={categoryVariant(system.category)}>
              {categoryLabel(system.category)}
            </Badge>
            {system.annex_iii_classification && (
              <div className="flex items-center gap-1 text-xs text-destructive">
                <ShieldAlert className="h-3 w-3" />
                Annex III
              </div>
            )}
          </div>
        </div>

        {system.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">{system.description}</p>
        )}

        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Completeness</p>
          <CompletenessBar score={system.completeness_score ?? 0} size="sm" showLabel />
        </div>

        <p className="text-xs text-muted-foreground">
          Updated {formatDate(system.updated_at)}
        </p>
      </CardContent>

      <CardFooter className="pt-0">
        <Link href={`/systems/${system.id}`} className="w-full">
          <Button variant="outline" size="sm" className="w-full">
            View system
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}
