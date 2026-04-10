'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, RefreshCw, Trash2, CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react'
import { integrationApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/components/ui/use-toast'
import { ConnectDialog } from '@/components/integrations/connect-dialog'
import type { Integration } from '@/types'

const TYPE_LABELS: Record<string, string> = {
  github: 'GitHub',
  gitlab: 'GitLab',
  mlflow: 'MLflow',
  wandb: 'Weights & Biases',
  webhook: 'Webhook',
  ci_cd: 'CI/CD',
}

const TYPE_COLORS: Record<string, string> = {
  github: 'bg-gray-900 text-white',
  gitlab: 'bg-orange-600 text-white',
  mlflow: 'bg-blue-600 text-white',
  wandb: 'bg-yellow-500 text-white',
  webhook: 'bg-purple-600 text-white',
  ci_cd: 'bg-green-600 text-white',
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'connected')
    return <CheckCircle2 className="h-4 w-4 text-green-500" />
  if (status === 'error')
    return <XCircle className="h-4 w-4 text-destructive" />
  return <AlertCircle className="h-4 w-4 text-muted-foreground" />
}

export default function IntegrationsPage() {
  const { id: systemId } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [showConnect, setShowConnect] = useState(false)

  // Get org_id from system query
  const { data: system } = useQuery({
    queryKey: ['system', systemId],
    queryFn: () =>
      fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/systems/${systemId}`,
        {
          headers: {
            Authorization: `Bearer ${typeof window !== 'undefined' ? localStorage.getItem('compliai_token') || '' : ''}`,
          },
        },
      ).then((r) => r.json()),
  })

  const orgId: string | undefined = system?.org_id

  const { data: integrations = [], isLoading } = useQuery({
    queryKey: ['integrations', orgId],
    queryFn: () => integrationApi.list(orgId!).then((r) => r.data),
    enabled: !!orgId,
  })

  const testMutation = useMutation({
    mutationFn: (integrationId: string) => integrationApi.test(orgId!, integrationId),
    onSuccess: (data) => {
      const result = data.data
      if (result.error) {
        toast({ variant: 'destructive', title: 'Connection failed', description: result.error })
      } else {
        toast({ title: 'Connection successful' })
      }
      queryClient.invalidateQueries({ queryKey: ['integrations', orgId] })
    },
    onError: () => toast({ variant: 'destructive', title: 'Test failed' }),
  })

  const syncMutation = useMutation({
    mutationFn: (integrationId: string) => integrationApi.sync(orgId!, integrationId),
    onSuccess: (data) => {
      if (data.data.error) {
        toast({ variant: 'destructive', title: 'Sync failed', description: data.data.error })
      } else {
        toast({ title: 'Sync complete' })
      }
      queryClient.invalidateQueries({ queryKey: ['integrations', orgId] })
    },
    onError: () => toast({ variant: 'destructive', title: 'Sync failed' }),
  })

  const deleteMutation = useMutation({
    mutationFn: (integrationId: string) => integrationApi.delete(orgId!, integrationId),
    onSuccess: () => {
      toast({ title: 'Integration removed' })
      queryClient.invalidateQueries({ queryKey: ['integrations', orgId] })
    },
    onError: () => toast({ variant: 'destructive', title: 'Delete failed' }),
  })

  if (isLoading || !orgId) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-muted rounded w-48" />
        <div className="h-32 bg-muted rounded" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Integrations</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Connect GitHub, GitLab, MLflow or W&amp;B to auto-populate your Annex IV documentation.
          </p>
        </div>
        <Button onClick={() => setShowConnect(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add integration
        </Button>
      </div>

      {integrations.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-10 w-10 text-muted-foreground mb-4" />
            <p className="font-medium">No integrations configured</p>
            <p className="text-sm text-muted-foreground mt-1">
              Connect a Git repo or MLOps platform to start syncing model metadata.
            </p>
            <Button className="mt-4" onClick={() => setShowConnect(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add first integration
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {integrations.map((cfg: Integration) => (
            <IntegrationCard
              key={cfg.id}
              cfg={cfg}
              onTest={() => testMutation.mutate(cfg.id)}
              onSync={() => syncMutation.mutate(cfg.id)}
              onDelete={() => {
                if (confirm(`Remove integration "${cfg.name}"?`)) {
                  deleteMutation.mutate(cfg.id)
                }
              }}
              isTesting={testMutation.isPending && testMutation.variables === cfg.id}
              isSyncing={syncMutation.isPending && syncMutation.variables === cfg.id}
              isDeleting={deleteMutation.isPending && deleteMutation.variables === cfg.id}
            />
          ))}
        </div>
      )}

      {/* Webhook instructions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">CI/CD Webhook</CardTitle>
          <CardDescription>
            Trigger automatic Technical File revision drafts from your deployment pipeline.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            POST to the endpoint below with deployment metadata. Set{' '}
            <code className="bg-muted px-1 rounded text-xs">X-Webhook-Token</code> to your webhook
            secret (configured in a Webhook / CI-CD integration above).
          </p>
          <div className="bg-muted rounded p-3 font-mono text-xs break-all">
            POST {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/systems/
            {systemId}/webhook
          </div>
          <p className="text-xs text-muted-foreground">
            Significant changes (version bumps, metric drops &gt;5%, dataset changes) will
            automatically create a new draft revision with pre-filled metadata.
          </p>
        </CardContent>
      </Card>

      {orgId && (
        <ConnectDialog
          open={showConnect}
          onOpenChange={setShowConnect}
          orgId={orgId}
          onCreated={() => {
            queryClient.invalidateQueries({ queryKey: ['integrations', orgId] })
            setShowConnect(false)
          }}
        />
      )}
    </div>
  )
}

function IntegrationCard({
  cfg,
  onTest,
  onSync,
  onDelete,
  isTesting,
  isSyncing,
  isDeleting,
}: {
  cfg: Integration
  onTest: () => void
  onSync: () => void
  onDelete: () => void
  isTesting: boolean
  isSyncing: boolean
  isDeleting: boolean
}) {
  const typeLabel = TYPE_LABELS[cfg.type] ?? cfg.type
  const typeBadgeClass = TYPE_COLORS[cfg.type] ?? 'bg-muted text-muted-foreground'

  return (
    <Card>
      <CardContent className="flex items-center justify-between py-4 gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <StatusIcon status={cfg.status} />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-medium truncate">{cfg.name}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${typeBadgeClass}`}>
                {typeLabel}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Status: <span className="capitalize">{cfg.status}</span>
              {cfg.last_sync_at && (
                <>{' · Last sync: '}{new Date(cfg.last_sync_at).toLocaleDateString()}</>
              )}
            </p>
            {cfg.error_message && (
              <p className="text-xs text-destructive mt-0.5 truncate">{cfg.error_message}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button size="sm" variant="outline" onClick={onTest} disabled={isTesting}>
            {isTesting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Test'}
          </Button>
          <Button size="sm" variant="outline" onClick={onSync} disabled={isSyncing}>
            {isSyncing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={onDelete}
            disabled={isDeleting}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
