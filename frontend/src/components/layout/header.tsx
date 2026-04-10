'use client'

import { useRouter } from 'next/navigation'
import { Bell, LogOut, User } from 'lucide-react'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface HeaderProps {
  breadcrumbs?: { label: string; href?: string }[]
}

export function Header({ breadcrumbs }: HeaderProps) {
  const router = useRouter()
  const { user, logout } = useAuthStore()

  function handleLogout() {
    logout()
    router.push('/auth/login')
  }

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b bg-card">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1 text-sm text-muted-foreground">
        {breadcrumbs?.map((bc, i) => (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && <span>/</span>}
            {bc.href ? (
              <a href={bc.href} className="hover:text-foreground transition-colors">
                {bc.label}
              </a>
            ) : (
              <span className="text-foreground font-medium">{bc.label}</span>
            )}
          </span>
        ))}
      </nav>

      <div className="flex items-center gap-2">
        {/* Notification bell */}
        <div className="relative">
          <Button variant="ghost" size="icon">
            <Bell className="h-4 w-4" />
          </Button>
          <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 flex items-center justify-center text-[10px]">
            0
          </Badge>
        </div>

        {/* User menu */}
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
            <User className="h-4 w-4 text-primary" />
          </div>
          <span className="text-sm font-medium hidden sm:block">{user?.full_name}</span>
        </div>

        <Button variant="ghost" size="icon" onClick={handleLogout} title="Sign out">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
