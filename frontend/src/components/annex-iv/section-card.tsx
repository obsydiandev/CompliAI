import { AlertTriangle, Edit } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CompletenessBar } from './completeness-bar'

interface SectionCardProps {
  sectionNumber: number
  sectionName: string
  completenessScore: number
  missingFields: string[]
  onEdit: () => void
}

export function SectionCard({
  sectionNumber,
  sectionName,
  completenessScore,
  missingFields,
  onEdit,
}: SectionCardProps) {
  return (
    <Card className="flex flex-col">
      <CardContent className="flex-1 flex flex-col gap-3 pt-5">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs shrink-0">
              §{sectionNumber}
            </Badge>
            <span className="text-sm font-medium leading-tight">{sectionName}</span>
          </div>
          <Button size="sm" variant="ghost" onClick={onEdit} className="shrink-0">
            <Edit className="h-3 w-3 mr-1" />
            Edit
          </Button>
        </div>

        <CompletenessBar score={completenessScore} size="sm" showLabel />

        {missingFields.length > 0 && (
          <div className="flex items-start gap-1.5 text-xs text-amber-700">
            <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-500" />
            <span>
              {missingFields.length} field{missingFields.length !== 1 ? 's' : ''} missing
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
