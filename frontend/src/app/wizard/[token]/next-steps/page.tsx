'use client'

import { useParams, useRouter } from 'next/navigation'
import { CheckCircle, XCircle, Lock, ArrowRight, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function WizardNextStepsPage() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-2xl mx-auto px-4 py-12 space-y-6">
        {/* Success header */}
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900">Your Technical File is ready</h1>
          <p className="text-slate-500 mt-2">You have completed the Annex IV Technical File structure.</p>
        </div>

        {/* Status panel */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Documentation Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Completed */}
            <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <div>
                  <p className="font-medium text-sm text-slate-900">Technical File Completion</p>
                  <p className="text-xs text-slate-500">All 7 blocks completed — PDF exported</p>
                </div>
              </div>
              <Badge className="bg-green-100 text-green-700 border border-green-300">100%</Badge>
            </div>

            {/* Locked in Lite */}
            <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center gap-3">
                <Lock className="w-5 h-5 text-slate-400" />
                <div>
                  <p className="font-medium text-sm text-slate-900">Evidence Validation</p>
                  <p className="text-xs text-slate-500">
                    Upload evidence, run automated checks — requires Pro
                  </p>
                </div>
              </div>
              <Badge className="bg-red-100 text-red-700 border border-red-300">NOT VERIFIED</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Honest message */}
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-6">
            <p className="font-semibold text-amber-900 mb-2">Your documentation is structurally complete, but not audit-ready.</p>
            <p className="text-sm text-amber-800 leading-relaxed">
              The Technical File you have generated covers all required Annex IV sections.
              However, structural completeness is not the same as evidence-backed conformity.
              A supervisory authority will also expect evidence artefacts, test results, and
              an up-to-date risk register.
            </p>
          </CardContent>
        </Card>

        {/* 3 next steps */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">3 next steps</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              {
                num: '1',
                title: 'Legal review',
                desc: 'Have a lawyer specialising in AI/tech law review the documentation before any regulatory submission.',
                color: 'bg-blue-100 text-blue-700',
              },
              {
                num: '2',
                title: 'ML Lead verification',
                desc: 'Confirm all technical details (accuracy metrics, validation methodology, data sources) with your ML engineer.',
                color: 'bg-purple-100 text-purple-700',
              },
              {
                num: '3',
                title: 'Keep it updated',
                desc: 'Art. 11(2) AI Act requires updating the Technical File whenever your AI system undergoes a substantial modification.',
                color: 'bg-green-100 text-green-700',
              },
            ].map(s => (
              <div key={s.num} className="flex items-start gap-3">
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${s.color}`}>
                  {s.num}
                </span>
                <div>
                  <p className="font-semibold text-sm">{s.title}</p>
                  <p className="text-sm text-slate-500 mt-0.5">{s.desc}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* CTA: Pro */}
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <p className="font-semibold text-slate-800 mb-1">
              When your model changes, come back for Pro.
            </p>
            <p className="text-sm text-slate-600 mb-4">
              Pro includes continuous monitoring via GitHub/GitLab, automated evidence collection,
              Audit Readiness Score, and collaborative review workflows.
            </p>
            <div className="flex gap-3">
              <Button variant="outline" size="sm" className="gap-1" onClick={() => router.push(`/wizard/${token}/export`)}>
                <RefreshCw className="w-4 h-4" /> Re-export PDF
              </Button>
              <Button size="sm" className="gap-1" onClick={() => router.push('/pricing')}>
                Learn about Pro <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Art. 72 reminder */}
        <p className="text-xs text-center text-slate-400">
          Under Art. 72 AI Act, providers of high-risk AI systems must review and update
          post-market monitoring at least once per year.
        </p>
      </div>
    </div>
  )
}
