'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, Mail, Hash, Webhook, Save, Plus, X } from 'lucide-react'
import { alertConfigApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from '@/components/ui/use-toast'
import type { AlertConfig } from '@/types'

export default function AlertConfigPage() {
  const { currentOrg } = useAuthStore()
  const orgId = currentOrg?.id
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['alert-config', orgId],
    queryFn: () => alertConfigApi.get(orgId!).then((r) => r.data),
    enabled: !!orgId,
  })

  const [form, setForm] = useState<AlertConfig | null>(null)
  const [newRecipient, setNewRecipient] = useState('')

  // Initialise form once data loads
  const config: AlertConfig = form ?? data ?? {
    email_enabled: false,
    email_recipients: [],
    slack_enabled: false,
    slack_webhook_url: '',
    webhook_enabled: false,
    webhook_url: '',
    min_severity: 'warning',
  }

  function patch(partial: Partial<AlertConfig>) {
    setForm({ ...config, ...partial })
  }

  const saveMutation = useMutation({
    mutationFn: (cfg: AlertConfig) => alertConfigApi.update(orgId!, cfg),
    onSuccess: () => {
      toast({ title: 'Alert configuration saved' })
      queryClient.invalidateQueries({ queryKey: ['alert-config', orgId] })
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to save' }),
  })

  function addRecipient() {
    const email = newRecipient.trim()
    if (!email || config.email_recipients.includes(email)) return
    patch({ email_recipients: [...config.email_recipients, email] })
    setNewRecipient('')
  }

  function removeRecipient(email: string) {
    patch({ email_recipients: config.email_recipients.filter((r) => r !== email) })
  }

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Bell className="h-6 w-6" />
          Alert Notifications
        </h1>
        <p className="text-muted-foreground mt-1">
          Configure where compliance violations are delivered.
        </p>
      </div>

      {/* Minimum severity */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Minimum Severity</CardTitle>
          <CardDescription>
            Alerts are only sent when a rule violation meets or exceeds this severity level.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            value={config.min_severity}
            onValueChange={(v) => patch({ min_severity: v as AlertConfig['min_severity'] })}
          >
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="info">Info</SelectItem>
              <SelectItem value="warning">Warning</SelectItem>
              <SelectItem value="blocking">Blocking only</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Email */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Mail className="h-4 w-4" />
                Email
              </CardTitle>
              <CardDescription>Send alerts to one or more email addresses.</CardDescription>
            </div>
            <Switch
              checked={config.email_enabled}
              onCheckedChange={(v: boolean) => patch({ email_enabled: v })}
            />
          </div>
        </CardHeader>
        {config.email_enabled && (
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Input
                placeholder="name@example.com"
                value={newRecipient}
                onChange={(e) => setNewRecipient(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addRecipient()}
                className="flex-1"
              />
              <Button variant="outline" size="sm" onClick={addRecipient}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {config.email_recipients.map((r) => (
                <span
                  key={r}
                  className="flex items-center gap-1 bg-muted text-sm px-2 py-0.5 rounded-full"
                >
                  {r}
                  <button
                    onClick={() => removeRecipient(r)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              {config.email_recipients.length === 0 && (
                <p className="text-xs text-muted-foreground">No recipients added yet.</p>
              )}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Slack */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Hash className="h-4 w-4" />
                Slack
              </CardTitle>
              <CardDescription>
                Post alerts to a Slack channel via an Incoming Webhook URL.
              </CardDescription>
            </div>
            <Switch
              checked={config.slack_enabled}
              onCheckedChange={(v: boolean) => patch({ slack_enabled: v })}
            />
          </div>
        </CardHeader>
        {config.slack_enabled && (
          <CardContent>
            <Label htmlFor="slack_webhook">Webhook URL</Label>
            <Input
              id="slack_webhook"
              placeholder="https://hooks.slack.com/services/…"
              value={config.slack_webhook_url}
              onChange={(e) => patch({ slack_webhook_url: e.target.value })}
              className="mt-1"
            />
          </CardContent>
        )}
      </Card>

      {/* Generic webhook */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Webhook className="h-4 w-4" />
                Webhook
              </CardTitle>
              <CardDescription>
                POST a JSON payload to any endpoint (e.g. Teams, PagerDuty, custom).
              </CardDescription>
            </div>
            <Switch
              checked={config.webhook_enabled}
              onCheckedChange={(v: boolean) => patch({ webhook_enabled: v })}
            />
          </div>
        </CardHeader>
        {config.webhook_enabled && (
          <CardContent>
            <Label htmlFor="webhook_url">Webhook URL</Label>
            <Input
              id="webhook_url"
              placeholder="https://your-endpoint.example.com/compliai"
              value={config.webhook_url}
              onChange={(e) => patch({ webhook_url: e.target.value })}
              className="mt-1"
            />
          </CardContent>
        )}
      </Card>

      <Button
        onClick={() => saveMutation.mutate(config)}
        disabled={saveMutation.isPending}
        className="w-full"
      >
        <Save className="h-4 w-4 mr-2" />
        {saveMutation.isPending ? 'Saving…' : 'Save Configuration'}
      </Button>
    </div>
  )
}
