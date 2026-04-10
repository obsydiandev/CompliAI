'use client'

import { useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ShieldCheck, Loader2, XCircle } from 'lucide-react'
import { useAuthStore } from '@/lib/auth'
import { authApi, ssoApi } from '@/lib/api'
import { toast } from '@/components/ui/use-toast'

/**
 * SSO callback page — handles the OAuth2 authorization code redirect.
 *
 * After the provider redirects here with ?code=…&state=…&provider=…
 * we POST to the backend callback endpoint and exchange the code for a JWT.
 */
export default function SSOCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const setToken = useAuthStore((s) => s.setToken)
  const setUser = useAuthStore((s) => s.setUser)
  const handledRef = useRef(false)

  useEffect(() => {
    if (handledRef.current) return
    handledRef.current = true

    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')
    // The provider is embedded in the URL pathname via the backend authorize URL
    // (e.g. /api/v1/sso/google/authorize) but after callback we don't have it.
    // We stored it in sessionStorage before the redirect.
    const provider = sessionStorage.getItem('sso_provider') || 'google'
    const redirectUri =
      (process.env.NEXT_PUBLIC_APP_URL || window.location.origin) + '/auth/sso/callback'

    async function handleCallback() {
      if (error) {
        toast({
          variant: 'destructive',
          title: 'SSO failed',
          description: error,
        })
        router.replace('/auth/login')
        return
      }

      if (!code || !state) {
        toast({ variant: 'destructive', title: 'Invalid SSO callback — missing code or state' })
        router.replace('/auth/login')
        return
      }

      try {
        const res = await ssoApi.callback(provider, { code, state, redirect_uri: redirectUri })
        setToken(res.data.access_token)

        const userRes = await authApi.me()
        setUser(userRes.data)

        sessionStorage.removeItem('sso_provider')
        router.replace(res.data.redirect_to || '/dashboard')
      } catch {
        toast({
          variant: 'destructive',
          title: 'SSO login failed',
          description: 'Could not complete the login. Please try again.',
        })
        router.replace('/auth/login')
      }
    }

    handleCallback()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const error = searchParams.get('error')

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-3">
          <XCircle className="h-10 w-10 text-destructive mx-auto" />
          <p className="text-lg font-medium">SSO login failed</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-2 mb-2">
          <ShieldCheck className="h-7 w-7 text-primary" />
          <span className="text-xl font-bold">CompliAI</span>
        </div>
        <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
        <p className="text-muted-foreground text-sm">Completing sign-in…</p>
      </div>
    </div>
  )
}
