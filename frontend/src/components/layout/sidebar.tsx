'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { LayoutDashboard, Cpu, Settings, ShieldCheck, LogOut, ChevronDown, BarChart3, Zap, Bell, Key } from 'lucide-react'
import { useAuthStore } from '@/lib/auth'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const navItems = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'AI Systems', href: '/systems', icon: Cpu },
  { label: 'Portfolio', href: '/dashboard/portfolio', icon: BarChart3 },
  { label: 'AI Usage', href: '/dashboard/llm-usage', icon: Zap },
  { label: 'Alert Config', href: '/dashboard/alert-config', icon: Bell },
  { label: 'API Keys', href: '/dashboard/api-keys', icon: Key },
  { label: 'Billing', href: '/dashboard/billing', icon: ShieldCheck },
  { label: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, currentOrg, logout } = useAuthStore()

  function handleLogout() {
    logout()
    router.push('/auth/login')
  }

  return (
    <aside className="flex flex-col w-64 shrink-0 border-r bg-card h-full">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 py-5 border-b">
        <ShieldCheck className="h-6 w-6 text-primary" />
        <span className="font-bold text-lg">CompliAI</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ label, href, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
              pathname.startsWith(href)
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>

      {/* Org switcher */}
      {currentOrg && (
        <div className="px-4 py-3 border-t">
          <button className="flex items-center justify-between w-full text-sm rounded-md px-2 py-1.5 hover:bg-accent transition-colors">
            <div className="text-left">
              <p className="font-medium truncate max-w-[160px]">{currentOrg.name}</p>
              <p className="text-xs text-muted-foreground capitalize">{currentOrg.plan}</p>
            </div>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
      )}

      {/* User + logout */}
      <div className="px-4 py-3 border-t flex items-center justify-between">
        <div className="text-sm overflow-hidden">
          <p className="font-medium truncate">{user?.full_name ?? 'User'}</p>
          <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={handleLogout} title="Sign out">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </aside>
  )
}
