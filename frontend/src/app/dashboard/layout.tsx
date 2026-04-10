'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/auth'
import { authApi, orgApi } from '@/lib/api'
import { Sidebar } from '@/components/layout/sidebar'
import { TrialBanner } from '@/components/billing/trial-banner'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { token, setUser, setCurrentOrg } = useAuthStore()

  useEffect(() => {
    if (!token) {
      router.replace('/auth/login')
      return
    }

    async function bootstrap() {
      try {
        const userRes = await authApi.me()
        setUser(userRes.data)

        const orgsRes = await orgApi.list()
        if (orgsRes.data.length > 0) {
          setCurrentOrg(orgsRes.data[0])
        }
      } catch {
        router.replace('/auth/login')
      }
    }

    bootstrap()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  if (!token) return null

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TrialBanner />
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">{children}</div>
        </main>
      </div>
    </div>
  )
}
