import { ChevronLeft, ChevronRight, CreditCard } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface Block {
  id: string
  number: number
  title: string
}

interface BlockNavigationProps {
  blocks: Block[]
  activeBlock: string
  onNavigate: (blockId: string) => void
  onCheckout: () => void
  completionPercent: number
  allComplete: boolean
}

export function BlockNavigation({
  blocks,
  activeBlock,
  onNavigate,
  onCheckout,
  completionPercent,
  allComplete,
}: BlockNavigationProps) {
  const currentIndex = blocks.findIndex(b => b.id === activeBlock)
  const isFirst = currentIndex === 0
  const isLast = currentIndex === blocks.length - 1

  return (
    <div className="flex items-center justify-between pt-4 border-t">
      <Button
        variant="ghost"
        disabled={isFirst}
        onClick={() => !isFirst && onNavigate(blocks[currentIndex - 1].id)}
        className="gap-1"
      >
        <ChevronLeft className="w-4 h-4" />
        {!isFirst ? `${blocks[currentIndex - 1].id}: ${blocks[currentIndex - 1].title}` : 'Back'}
      </Button>

      <div className="text-center">
        <p className="text-xs text-slate-500">Technical File Completion</p>
        <p className="text-lg font-bold text-slate-900">{completionPercent}%</p>
      </div>

      {isLast && allComplete ? (
        <Button onClick={onCheckout} className="gap-2">
          <CreditCard className="w-4 h-4" />
          Export PDF — €299
        </Button>
      ) : (
        <Button
          disabled={isLast}
          onClick={() => !isLast && onNavigate(blocks[currentIndex + 1].id)}
          className="gap-1"
        >
          {!isLast ? `${blocks[currentIndex + 1].id}: ${blocks[currentIndex + 1].title}` : 'Done'}
          <ChevronRight className="w-4 h-4" />
        </Button>
      )}
    </div>
  )
}
