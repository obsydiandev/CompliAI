'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/auth'
import { ShieldCheck } from 'lucide-react'

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const user = useAuthStore((s) => s.user)
  const token = useAuthStore((s) => s.token)

  useEffect(() => {
    if (!token) {
      router.replace('/auth/login')
      return
    }
    // Superuser check is enforced server-side too; this is just UX guard
    if (user && !user.is_active) {
      router.replace('/dashboard')
    }
  }, [token, user, router])

  if (!token) return null

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card px-6 py-4 flex items-center gap-3">
        <ShieldCheck className="h-5 w-5 text-primary" />
        <span className="font-bold">CompliAI Admin</span>
        <span className="text-xs text-muted-foreground ml-2 bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
          Internal — not for customers
        </span>
      </header>
      <main className="p-6">{children}</main>
    </div>
  )
}
