import { File, Link as LinkIcon, FileBarChart, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatDate, truncate } from '@/lib/utils'
import type { EvidenceAttachment, EvidenceType } from '@/types'

function typeIcon(type: EvidenceType) {
  if (type === 'file') return <File className="h-4 w-4" />
  if (type === 'url') return <LinkIcon className="h-4 w-4" />
  return <FileBarChart className="h-4 w-4" />
}

interface EvidenceListProps {
  evidence: EvidenceAttachment[]
  onDelete: (id: string) => void
  onAdd?: () => void
}

export function EvidenceList({ evidence, onDelete }: EvidenceListProps) {
  if (evidence.length === 0) {
    return (
      <div className="text-center py-6 text-sm text-muted-foreground">
        <p>No evidence attached yet.</p>
      </div>
    )
  }

  return (
    <ul className="divide-y text-sm">
      {evidence.map((item) => (
        <li key={item.id} className="flex items-start gap-3 py-3">
          <span className="mt-0.5 text-muted-foreground">{typeIcon(item.type)}</span>
          <div className="flex-1 min-w-0 space-y-0.5">
            <p className="font-medium truncate">
              {item.filename ?? (item.url ? truncate(item.url, 50) : 'Untitled')}
            </p>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline" className="text-xs">
                {item.type}
              </Badge>
              {item.source && (
                <span className="text-xs text-muted-foreground">{item.source}</span>
              )}
              {item.version && (
                <span className="text-xs text-muted-foreground">v{item.version}</span>
              )}
              <span className="text-xs text-muted-foreground">
                {formatDate(item.uploaded_at)}
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0 text-muted-foreground hover:text-destructive"
            onClick={() => onDelete(item.id)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </li>
      ))}
    </ul>
  )
}
