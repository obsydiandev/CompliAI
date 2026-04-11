'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { FileText, ArrowRight, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/components/ui/use-toast'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function WizardEntryPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [orgName, setOrgName] = useState('')
  const [systemName, setSystemName] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const startWizard = async (skipEmail = false) => {
    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/wizard/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: skipEmail ? null : email || null,
          org_name: orgName || null,
          system_name: systemName || null,
        }),
      })
      if (!res.ok) throw new Error('Failed to create session')
      const data = await res.json()
      router.push(`/wizard/${data.session_token}`)
    } catch {
      toast({ title: 'Error', description: 'Failed to start wizard. Please try again.', variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-2xl mx-auto px-4 py-16">
        {/* Hero */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full mb-6">
            <FileText className="w-4 h-4" />
            Annex IV Technical File — EU AI Act
          </div>
          <h1 className="text-4xl font-bold text-slate-900 mb-4">
            Generate your Annex IV<br />Technical File in 60 minutes
          </h1>
          <p className="text-lg text-slate-600">
            7-step wizard. AI-assisted drafting. PDF export.
            <br />No technical knowledge required.
          </p>
        </div>

        {/* What you get */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          {[
            { icon: '📋', title: '9 Annex IV sections', desc: 'All required sections covered' },
            { icon: '🤖', title: 'AI drafting', desc: 'LLM generates formal paragraphs from your answers' },
            { icon: '📄', title: 'PDF export', desc: 'Print-ready with mandatory disclaimer' },
          ].map(f => (
            <Card key={f.title} className="text-center">
              <CardContent className="pt-6">
                <div className="text-3xl mb-2">{f.icon}</div>
                <p className="font-semibold text-sm">{f.title}</p>
                <p className="text-xs text-slate-500 mt-1">{f.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Entry form */}
        <Card>
          <CardHeader>
            <CardTitle>Get started</CardTitle>
            <p className="text-sm text-slate-500">
              Optional — you can fill in these details later. Your session is saved for 7 days.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">AI System Name</label>
              <Input
                placeholder="e.g. CreditScore AI v2.0"
                value={systemName}
                onChange={e => setSystemName(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Organisation Name</label>
              <Input
                placeholder="e.g. ACME Financial Technologies"
                value={orgName}
                onChange={e => setOrgName(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">
                Email <span className="text-slate-400 font-normal">(optional — to resume later)</span>
              </label>
              <Input
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
            </div>

            <Button
              className="w-full gap-2"
              size="lg"
              disabled={isLoading}
              onClick={() => startWizard(false)}
            >
              {isLoading ? 'Creating session…' : 'Start Technical File'} <ChevronRight className="w-4 h-4" />
            </Button>
            <button
              className="w-full text-sm text-slate-400 hover:text-slate-600 text-center"
              onClick={() => startWizard(true)}
            >
              Skip — start without email
            </button>
          </CardContent>
        </Card>

        {/* Pricing */}
        <div className="text-center mt-8">
          <p className="text-2xl font-bold text-slate-900">€299 <span className="text-base font-normal text-slate-500">one-time</span></p>
          <p className="text-sm text-slate-500 mt-1">Pay only when you export the PDF. No subscription required.</p>
        </div>

        {/* Disclaimer preview */}
        <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs text-amber-800 leading-relaxed">
            <strong>Important:</strong> Technical File Completion % means structural completeness only.
            The exported document requires review by a qualified legal professional and your ML Lead
            before submission to any supervisory authority.
          </p>
        </div>
      </div>
    </div>
  )
}
