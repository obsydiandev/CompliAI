'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Download, AlertTriangle, CheckSquare, Square, Loader2, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/use-toast'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const DISCLAIMER_TEXT =
  'Technical File Completion % means structural completeness only — this document was generated on the basis of information provided by the system owner and has not been independently verified. It requires review by a qualified legal professional and the ML Lead before submission to any supervisory authority. CompliAI provides a documentation tool, not legal advice.'

export default function WizardExportPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = params.token as string

  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [session, setSession] = useState<{ payment_confirmed: boolean; system_name: string | null } | null>(null)
  const [logoFile, setLogoFile] = useState<File | null>(null)

  const paymentStatus = searchParams.get('payment')

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/wizard/sessions/${token}`)
      .then(r => r.json())
      .then(setSession)
  }, [token])

  const handleExport = async () => {
    if (!disclaimerAccepted) return

    setIsExporting(true)
    try {
      const formData = new FormData()
      formData.append('disclaimer_accepted', 'true')
      if (logoFile) formData.append('logo', logoFile)

      const res = await fetch(
        `${API_BASE}/api/v1/wizard/sessions/${token}/export-pdf?disclaimer_accepted=true`,
        { method: 'POST', body: formData }
      )

      if (res.status === 402) {
        toast({ title: 'Payment required', description: 'Please complete payment first.', variant: 'destructive' })
        router.push(`/wizard/${token}/checkout`)
        return
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Export failed')
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `annex-iv-${(session?.system_name || 'draft').toLowerCase().replace(/\s+/g, '-')}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      // Navigate to next steps
      router.push(`/wizard/${token}/next-steps`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Export failed'
      toast({ title: 'Export failed', description: msg, variant: 'destructive' })
    } finally {
      setIsExporting(false)
    }
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-2xl mx-auto px-4 py-12 space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-slate-900">Export Annex IV Technical File</h1>
          <p className="text-slate-500 mt-2">
            {session.system_name ? `Technical File for: ${session.system_name}` : 'Your AI system'}
          </p>
        </div>

        {paymentStatus === 'success' && (
          <Card className="bg-green-50 border-green-200">
            <CardContent className="pt-4">
              <p className="text-green-800 font-medium text-center">✅ Payment confirmed — you can now export your PDF.</p>
            </CardContent>
          </Card>
        )}

        {/* Logo upload */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Upload className="w-4 h-4" /> Logo (Optional)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <label className="block text-sm text-slate-600 mb-2">
              Upload your organisation logo to include in the PDF header.
            </label>
            <Input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={e => setLogoFile(e.target.files?.[0] || null)}
            />
            {logoFile && <p className="text-xs text-green-600 mt-1">✓ {logoFile.name}</p>}
          </CardContent>
        </Card>

        {/* MANDATORY DISCLAIMER — non-skippable */}
        <Card className="border-2 border-amber-300 bg-amber-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-amber-900 mb-2">Important Disclaimer — Please Read</p>
                <p className="text-sm text-amber-800 leading-relaxed">{DISCLAIMER_TEXT}</p>
              </div>
            </div>

            {/* Mandatory checkbox — export disabled until checked */}
            <button
              className="flex items-start gap-3 mt-4 text-left w-full"
              onClick={() => setDisclaimerAccepted(!disclaimerAccepted)}
            >
              {disclaimerAccepted ? (
                <CheckSquare className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              ) : (
                <Square className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
              )}
              <span className="text-sm text-slate-700">
                I understand and accept that this document requires legal and ML Lead review before submission
                to any supervisory authority. This is a draft Technical File, not a certified compliance document.
              </span>
            </button>
          </CardContent>
        </Card>

        {/* Export button — disabled until disclaimer accepted */}
        <Button
          size="lg"
          className="w-full gap-2"
          disabled={!disclaimerAccepted || isExporting || !session.payment_confirmed}
          onClick={handleExport}
        >
          {isExporting ? (
            <><Loader2 className="w-5 h-5 animate-spin" />Generating PDF…</>
          ) : (
            <><Download className="w-5 h-5" />Download Annex IV PDF</>
          )}
        </Button>

        {!disclaimerAccepted && (
          <p className="text-center text-sm text-slate-500">
            You must accept the disclaimer above before exporting.
          </p>
        )}

        {!session.payment_confirmed && (
          <Card className="border-blue-200 bg-blue-50 text-center">
            <CardContent className="pt-4 pb-4">
              <p className="text-sm text-blue-800 mb-3">Payment required to download the PDF.</p>
              <Button onClick={() => router.push(`/wizard/${token}/checkout`)}>
                Complete Payment — €299
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
