'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useAuthStore } from '@/lib/auth'
import { systemApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { SystemCard } from '@/components/systems/system-card'

function SkeletonCard() {
  return (
    <div className="rounded-lg border bg-card p-6 space-y-4 animate-pulse">
      <div className="h-4 bg-muted rounded w-3/4" />
      <div className="h-3 bg-muted rounded w-1/2" />
      <div className="h-2 bg-muted rounded w-full" />
    </div>
  )
}

export default function DashboardPage() {
  const currentOrg = useAuthStore((s) => s.currentOrg)

  const { data: systems, isLoading } = useQuery({
    queryKey: ['systems', currentOrg?.id],
    queryFn: () => systemApi.list(currentOrg!.id).then((r) => r.data),
    enabled: !!currentOrg,
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Systems</h1>
          <p className="text-muted-foreground text-sm">
            {currentOrg ? currentOrg.name : 'Loading organisation…'}
          </p>
        </div>
        <Link href="/systems/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add AI System
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : !systems || systems.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center space-y-4">
          <div className="text-4xl">🛡️</div>
          <h2 className="text-xl font-semibold">No AI systems yet</h2>
          <p className="text-muted-foreground max-w-sm">
            Add your first high-risk AI system to start managing your EU AI Act compliance
            technical file.
          </p>
          <Link href="/systems/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add AI System
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {systems.map((system) => (
            <SystemCard key={system.id} system={system} />
          ))}
        </div>
      )}
    </div>
  )
}
