import { AlertTriangle, CheckCircle, Shield } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface RiskBadgeInlineProps {
  riskLevel: string
  justification?: string
  compact?: boolean
}

const RISK_CONFIG = {
  high_risk: {
    label: 'High Risk',
    badgeColor: 'bg-red-100 text-red-800 border border-red-300',
    containerColor: 'bg-red-50 border-red-200',
    icon: AlertTriangle,
    iconColor: 'text-red-600',
    description: 'Annex III high-risk — Annex IV Technical File required',
  },
  limited_risk: {
    label: 'Limited Risk',
    badgeColor: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
    containerColor: 'bg-yellow-50 border-yellow-200',
    icon: Shield,
    iconColor: 'text-yellow-600',
    description: 'Transparency obligations apply (Art. 52)',
  },
  minimal_risk: {
    label: 'Minimal Risk',
    badgeColor: 'bg-green-100 text-green-800 border border-green-300',
    containerColor: 'bg-green-50 border-green-200',
    icon: CheckCircle,
    iconColor: 'text-green-600',
    description: 'No mandatory documentation required',
  },
}

export function RiskBadgeInline({ riskLevel, justification, compact = false }: RiskBadgeInlineProps) {
  const cfg = RISK_CONFIG[riskLevel as keyof typeof RISK_CONFIG] ?? RISK_CONFIG.minimal_risk
  const Icon = cfg.icon

  if (compact) {
    return (
      <span className={cn('inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full', cfg.badgeColor)}>
        <Icon className={cn('w-3 h-3', cfg.iconColor)} />
        {cfg.label}
      </span>
    )
  }

  return (
    <div className={cn('flex items-start gap-3 p-4 rounded-lg border', cfg.containerColor)}>
      <Icon className={cn('w-5 h-5 mt-0.5 flex-shrink-0', cfg.iconColor)} />
      <div>
        <div className="flex items-center gap-2">
          <Badge className={cfg.badgeColor}>{cfg.label}</Badge>
          <span className="text-sm text-slate-600">{cfg.description}</span>
        </div>
        {justification && (
          <p className="text-sm text-slate-700 mt-1 leading-relaxed">{justification}</p>
        )}
      </div>
    </div>
  )
}
