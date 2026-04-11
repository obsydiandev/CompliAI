'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { CreditCard, Loader2 } from 'lucide-react'
import { toast } from '@/components/ui/use-toast'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function WizardCheckoutPage() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string

  useEffect(() => {
    initiateCheckout()
  }, [])

  const initiateCheckout = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/wizard/sessions/${token}/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (!res.ok) throw new Error('Checkout failed')
      const data = await res.json()

      if (data.mock) {
        // Development mode: skip to export
        router.push(`/wizard/${token}/export?payment=mock`)
        return
      }

      if (data.checkout_url) {
        window.location.href = data.checkout_url
      }
    } catch {
      toast({
        title: 'Checkout error',
        description: 'Could not initiate payment. Please try again.',
        variant: 'destructive',
      })
      router.push(`/wizard/${token}`)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
          <CreditCard className="w-8 h-8 text-blue-600" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Redirecting to payment…</h1>
        <p className="text-slate-500">You will be redirected to our secure payment page.</p>
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 mx-auto" />
      </div>
    </div>
  )
}
