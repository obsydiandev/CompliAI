import { cn, formatPercent } from '@/lib/utils'

interface CompletenessBarProps {
  score: number
  size?: 'sm' | 'default' | 'lg'
  showLabel?: boolean
}

function barColor(score: number) {
  if (score >= 0.66) return 'bg-green-500'
  if (score >= 0.33) return 'bg-yellow-500'
  return 'bg-red-500'
}

function labelColor(score: number) {
  if (score >= 0.66) return 'text-green-700'
  if (score >= 0.33) return 'text-yellow-700'
  return 'text-red-700'
}

const heightMap = { sm: 'h-1.5', default: 'h-2.5', lg: 'h-4' }

export function CompletenessBar({
  score,
  size = 'default',
  showLabel = true,
}: CompletenessBarProps) {
  const height = heightMap[size]
  const pct = Math.round(score * 100)

  return (
    <div className="flex items-center gap-2">
      <div className={cn('relative flex-1 overflow-hidden rounded-full bg-secondary', height)}>
        <div
          className={cn('h-full transition-all', barColor(score))}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className={cn('text-xs font-medium w-10 text-right', labelColor(score))}>
          {formatPercent(score)}
        </span>
      )}
    </div>
  )
}
