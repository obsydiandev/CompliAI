'use client'

import { Calendar, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface Milestone {
  date: string
  label: string
  description: string
  article_ref: string
  days_remaining: number
  urgency: 'past' | 'green' | 'orange' | 'red'
}

interface PanicCalendarProps {
  milestones: Milestone[]
  className?: string
}

const URGENCY_CONFIG = {
  past: {
    bar: 'bg-slate-300',
    badge: 'bg-slate-100 text-slate-500',
    border: 'border-slate-200',
    label: 'Passed',
  },
  green: {
    bar: 'bg-green-500',
    badge: 'bg-green-100 text-green-700',
    border: 'border-green-200',
    label: (days: number) => `${days} days`,
  },
  orange: {
    bar: 'bg-orange-400',
    badge: 'bg-orange-100 text-orange-700',
    border: 'border-orange-200',
    label: (days: number) => `⚠ ${days} days`,
  },
  red: {
    bar: 'bg-red-500',
    badge: 'bg-red-100 text-red-700',
    border: 'border-red-200',
    label: (days: number) => `🔴 ${days} days`,
  },
}

export function PanicCalendar({ milestones, className }: PanicCalendarProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Calendar className="w-5 h-5 text-blue-600" />
          EU AI Act Deadline Calendar
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {milestones.map((m) => {
          const cfg = URGENCY_CONFIG[m.urgency]
          const labelFn = typeof cfg.label === 'function' ? cfg.label : () => cfg.label as string
          return (
            <div
              key={m.date}
              className={cn(
                'flex items-start gap-3 p-3 border rounded-lg',
                cfg.border,
                m.urgency === 'past' ? 'opacity-60' : ''
              )}
            >
              <div className={cn('mt-1 w-3 h-3 rounded-full flex-shrink-0', cfg.bar)} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <p className="font-medium text-sm text-slate-900">{m.label}</p>
                  <span className={cn('text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap', cfg.badge)}>
                    {labelFn(m.days_remaining)}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{m.date}</p>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{m.description}</p>
                <p className="text-xs font-mono text-slate-400 mt-1">{m.article_ref}</p>
              </div>
            </div>
          )
        })}

        <p className="text-xs text-slate-400 mt-2 text-center">
          Dates based on Regulation (EU) 2024/1689 — verify with your legal counsel.
        </p>
      </CardContent>
    </Card>
  )
}
