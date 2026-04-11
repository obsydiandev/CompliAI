import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PanicCalendar } from '@/components/classifier/PanicCalendar'
import { cn } from '@/lib/utils'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Props {
  params: { token: string }
}

async function getResult(token: string) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/classifier/result/${token}`, {
      next: { revalidate: 3600 },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const result = await getResult(params.token)
  if (!result) return { title: 'AI Act Risk Classification — CompliAI' }

  const riskLabel =
    result.risk_level === 'high_risk'
      ? 'High-Risk'
      : result.risk_level === 'limited_risk'
      ? 'Limited-Risk'
      : 'Minimal-Risk'

  return {
    title: `${riskLabel} AI System — EU AI Act Classification | CompliAI`,
    description: result.justification?.slice(0, 160),
    openGraph: {
      title: `My AI system is classified as ${riskLabel} under the EU AI Act`,
      description: result.justification?.slice(0, 200),
      images: ['/og-classifier.png'],
    },
    twitter: {
      card: 'summary_large_image',
      title: `${riskLabel} AI System — EU AI Act Classification`,
    },
  }
}

const RISK_CONFIG = {
  high_risk: {
    label: 'High Risk',
    color: 'bg-red-100 text-red-800 border-red-300',
    Icon: AlertTriangle,
    iconColor: 'text-red-600',
  },
  limited_risk: {
    label: 'Limited Risk',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    Icon: Shield,
    iconColor: 'text-yellow-600',
  },
  minimal_risk: {
    label: 'Minimal Risk',
    color: 'bg-green-100 text-green-800 border-green-300',
    Icon: CheckCircle,
    iconColor: 'text-green-600',
  },
}

export default async function ClassifierResultPage({ params }: Props) {
  const result = await getResult(params.token)
  if (!result) notFound()

  const cfg = RISK_CONFIG[result.risk_level as keyof typeof RISK_CONFIG] ?? RISK_CONFIG.minimal_risk
  const { Icon } = cfg

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-6">
        <div className="text-center">
          <p className="text-sm text-slate-500 mb-2">AI Act Risk Classification</p>
          <h1 className="text-3xl font-bold text-slate-900">EU AI Act Risk Assessment Result</h1>
        </div>

        <Card className="border-2">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <Icon className={cn('w-8 h-8 mt-1 flex-shrink-0', cfg.iconColor)} />
              <div>
                <Badge className={cn('mb-2', cfg.color)}>{cfg.label}</Badge>
                <p className="text-base text-slate-700 leading-relaxed">{result.justification}</p>
                {result.article_citations?.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {result.article_citations.map((c: string) => (
                      <span key={c} className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-1 rounded">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {result.panic_calendar && <PanicCalendar milestones={result.panic_calendar} />}

        <Card className="border-blue-200 bg-blue-50 text-center">
          <CardContent className="pt-6 pb-6">
            <p className="font-semibold text-slate-800 mb-3">Need an Annex IV Technical File?</p>
            <a
              href="/wizard"
              className="inline-block bg-blue-600 text-white font-bold px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Generate Technical File — €299
            </a>
            <p className="text-xs text-slate-500 mt-3">
              Under 60 minutes. AI-assisted drafting. PDF export with mandatory disclaimer.
            </p>
          </CardContent>
        </Card>

        <p className="text-xs text-center text-slate-400">
          Classified {result.created_at ? new Date(result.created_at).toLocaleDateString('en-GB') : ''} using
          CompliAI AI Act Classifier. Not legal advice.
        </p>
      </div>
    </div>
  )
}
