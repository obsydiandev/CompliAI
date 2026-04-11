'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Key, Plus, Trash2, Copy, Eye, EyeOff, CheckCircle } from 'lucide-react'
import { apiKeyApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/components/ui/use-toast'
import type { ApiKeyCreated, ApiKeyRead } from '@/types'

export default function ApiKeysPage() {
  const { currentOrg } = useAuthStore()
  const orgId = currentOrg?.id
  const queryClient = useQueryClient()

  const [showCreate, setShowCreate] = useState(false)
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null)
  const [showKey, setShowKey] = useState(false)
  const [copied, setCopied] = useState(false)

  const { data: keys = [], isLoading } = useQuery({
    queryKey: ['api-keys', orgId],
    queryFn: () => apiKeyApi.list(orgId!).then((r) => r.data),
    enabled: !!orgId,
  })

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) => apiKeyApi.revoke(orgId!, keyId),
    onSuccess: () => {
      toast({ title: 'API key revoked' })
      queryClient.invalidateQueries({ queryKey: ['api-keys', orgId] })
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to revoke key' }),
  })

  function copyKey(key: string) {
    navigator.clipboard.writeText(key).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Key className="h-6 w-6" />
            API Keys
          </h1>
          <p className="text-muted-foreground mt-1">
            Programmatic access to CompliAI for integrations and automation.
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New API Key
        </Button>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading…</p>
      ) : keys.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Key className="h-10 w-10 mx-auto text-muted-foreground/40 mb-3" />
            <p className="text-muted-foreground">No API keys yet.</p>
            <Button className="mt-4" variant="outline" onClick={() => setShowCreate(true)}>
              Create your first key
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {keys.map((k) => (
            <ApiKeyCard
              key={k.id}
              apiKey={k}
              onRevoke={() => revokeMutation.mutate(k.id)}
              isRevoking={revokeMutation.isPending}
            />
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Authentication</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">
            Pass your API key in the <code className="bg-muted px-1 rounded text-xs">X-API-Key</code> header:
          </p>
          <div className="bg-muted rounded p-3 font-mono text-xs break-all">
            curl -H &quot;X-API-Key: caik_…&quot; {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/…
          </div>
        </CardContent>
      </Card>

      {/* Create dialog */}
      <CreateKeyDialog
        open={showCreate}
        orgId={orgId ?? ''}
        onCreated={(k) => {
          setCreatedKey(k)
          setShowCreate(false)
          queryClient.invalidateQueries({ queryKey: ['api-keys', orgId] })
        }}
        onClose={() => setShowCreate(false)}
      />

      {/* Reveal new key dialog */}
      {createdKey && (
        <Dialog open onOpenChange={() => setCreatedKey(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>API Key Created</DialogTitle>
              <DialogDescription>
                Copy this key now — it will <strong>not</strong> be shown again.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <div className="relative">
                <Input
                  readOnly
                  value={showKey ? createdKey.key : '•'.repeat(40)}
                  className="pr-20 font-mono text-sm"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7"
                    onClick={() => setShowKey((v) => !v)}
                  >
                    {showKey ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7"
                    onClick={() => copyKey(createdKey.key)}
                  >
                    {copied ? (
                      <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Key prefix: <code className="bg-muted px-1 rounded">{createdKey.key_prefix}…</code>
              </p>
            </div>
            <DialogFooter>
              <Button onClick={() => setCreatedKey(null)}>Done</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

function ApiKeyCard({
  apiKey,
  onRevoke,
  isRevoking,
}: {
  apiKey: ApiKeyRead
  onRevoke: () => void
  isRevoking: boolean
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between py-4">
        <div className="space-y-0.5">
          <p className="font-medium">{apiKey.name}</p>
          <p className="text-xs text-muted-foreground font-mono">
            {apiKey.key_prefix}…
            {apiKey.last_used_at && (
              <> · Last used: {new Date(apiKey.last_used_at).toLocaleDateString()}</>
            )}
            {apiKey.expires_at && (
              <> · Expires: {new Date(apiKey.expires_at).toLocaleDateString()}</>
            )}
          </p>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={onRevoke}
          disabled={isRevoking}
          className="text-destructive hover:text-destructive"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  )
}

function CreateKeyDialog({
  open,
  orgId,
  onCreated,
  onClose,
}: {
  open: boolean
  orgId: string
  onCreated: (key: ApiKeyCreated) => void
  onClose: () => void
}) {
  const [name, setName] = useState('')
  const [expireDays, setExpireDays] = useState('')

  const createMutation = useMutation({
    mutationFn: () =>
      apiKeyApi
        .create(orgId, {
          name,
          expires_in_days: expireDays ? parseInt(expireDays, 10) : null,
        })
        .then((r) => r.data),
    onSuccess: (data) => {
      onCreated(data)
      setName('')
      setExpireDays('')
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to create key' }),
  })

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create API Key</DialogTitle>
          <DialogDescription>Give your key a descriptive name.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="key-name">Name</Label>
            <Input
              id="key-name"
              placeholder="e.g. CI/CD pipeline, Integration test"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="expire-days">Expiry (days, leave blank for no expiry)</Label>
            <Input
              id="expire-days"
              type="number"
              placeholder="e.g. 90"
              value={expireDays}
              onChange={(e) => setExpireDays(e.target.value)}
              className="mt-1"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={() => createMutation.mutate()}
            disabled={!name.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating…' : 'Create Key'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
