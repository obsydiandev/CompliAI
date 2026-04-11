'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Users, FileText, CheckCircle, Clock, Send, Eye, Plus, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/use-toast'
import { useAuthStore } from '@/lib/auth'
import { cn } from '@/lib/utils'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ClientSession {
  session_token: string
  client_name: string
  system_name: string | null
  email: string | null
  status: 'generated' | 'in_review' | 'approved' | 'sent'
  payment_confirmed: boolean
  completion_percent: number
  created_at: string | null
}

interface Partner {
  partner_id: string
  name: string
  org_id: string
  has_logo: boolean
  client_count: number
}

const STATUS_CONFIG = {
  generated: { label: 'Generated', color: 'bg-blue-100 text-blue-700', icon: FileText },
  in_review: { label: 'In Review', color: 'bg-yellow-100 text-yellow-700', icon: Eye },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  sent: { label: 'Sent to Client', color: 'bg-purple-100 text-purple-700', icon: Send },
}

const STATUS_FLOW: ClientSession['status'][] = ['generated', 'in_review', 'approved', 'sent']

export default function PartnerDashboardPage() {
  const router = useRouter()
  const currentOrg = useAuthStore(s => s.currentOrg)
  const token = useAuthStore(s => s.token)

  const [partner, setPartner] = useState<Partner | null>(null)
  const [clients, setClients] = useState<ClientSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [newClientName, setNewClientName] = useState('')
  const [newSystemName, setNewSystemName] = useState('')
  const [showNewClient, setShowNewClient] = useState(false)

  useEffect(() => {
    if (currentOrg) loadPartner()
  }, [currentOrg])

  const authHeaders = { Authorization: `Bearer ${token}` }

  const loadPartner = async () => {
    try {
      // Register or get partner
      const regRes = await fetch(`${API_BASE}/api/v1/partners`, {
        method: 'POST',
        headers: { ...authHeaders, 'Content-Type': 'application/json' },
        body: JSON.stringify({ org_id: currentOrg!.id, name: currentOrg!.name }),
      })
      const partnerData = await regRes.json()
      setPartner(partnerData)

      // Load clients
      const clientRes = await fetch(
        `${API_BASE}/api/v1/partners/${partnerData.partner_id}/clients`,
        { headers: authHeaders }
      )
      const clientData = await clientRes.json()
      setClients(clientData.clients || [])
    } catch {
      toast({ title: 'Error', description: 'Failed to load partner account.', variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }

  const createClient = async () => {
    if (!partner || !newClientName) return
    setIsCreating(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/partners/${partner.partner_id}/clients`, {
        method: 'POST',
        headers: { ...authHeaders, 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_name: newClientName, system_name: newSystemName || null }),
      })
      const data = await res.json()
      setClients(prev => [...prev, {
        session_token: data.session_token,
        client_name: newClientName,
        system_name: newSystemName || null,
        email: null,
        status: 'generated',
        payment_confirmed: true,
        completion_percent: 0,
        created_at: new Date().toISOString(),
      }])
      setNewClientName('')
      setNewSystemName('')
      setShowNewClient(false)
      toast({ title: 'Client created', description: `Wizard started for ${newClientName}` })
    } catch {
      toast({ title: 'Error', description: 'Failed to create client.', variant: 'destructive' })
    } finally {
      setIsCreating(false)
    }
  }

  const updateStatus = async (sessionToken: string, newStatus: ClientSession['status']) => {
    if (!partner) return
    try {
      await fetch(`${API_BASE}/api/v1/partners/${partner.partner_id}/clients/${sessionToken}/status`, {
        method: 'PUT',
        headers: { ...authHeaders, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      setClients(prev => prev.map(c =>
        c.session_token === sessionToken ? { ...c, status: newStatus } : c
      ))
    } catch {
      toast({ title: 'Error', description: 'Failed to update status.', variant: 'destructive' })
    }
  }

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin" /></div>
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Partner Dashboard</h1>
          <p className="text-slate-500 mt-1">{partner?.name} — White-Label Technical File Generator</p>
        </div>
        <Button onClick={() => setShowNewClient(true)} className="gap-2">
          <Plus className="w-4 h-4" /> Add Client
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        {STATUS_FLOW.map(s => {
          const count = clients.filter(c => c.status === s).length
          const cfg = STATUS_CONFIG[s]
          return (
            <Card key={s}>
              <CardContent className="pt-4">
                <p className={cn('text-xs font-medium px-2 py-0.5 rounded-full w-fit mb-1', cfg.color)}>{cfg.label}</p>
                <p className="text-2xl font-bold">{count}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* New client form */}
      {showNewClient && (
        <Card className="mb-6 border-blue-200">
          <CardHeader><CardTitle className="text-base">New Client Technical File</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Client name / company" value={newClientName} onChange={e => setNewClientName(e.target.value)} />
            <Input placeholder="AI system name (optional)" value={newSystemName} onChange={e => setNewSystemName(e.target.value)} />
            <div className="flex gap-2">
              <Button onClick={createClient} disabled={!newClientName || isCreating} className="gap-1">
                {isCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Create
              </Button>
              <Button variant="outline" onClick={() => setShowNewClient(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Client list */}
      <div className="space-y-3">
        {clients.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-slate-400">
              <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No clients yet. Add your first client to get started.</p>
            </CardContent>
          </Card>
        )}
        {clients.map(client => {
          const cfg = STATUS_CONFIG[client.status]
          const StatusIcon = cfg.icon
          const currentIdx = STATUS_FLOW.indexOf(client.status)
          return (
            <Card key={client.session_token} className="hover:shadow-sm transition-shadow">
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-slate-900">{client.client_name}</p>
                      <Badge className={cn('text-xs', cfg.color)}>
                        <StatusIcon className="w-3 h-3 mr-1" />{cfg.label}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-500">{client.system_name || 'No system name'}</p>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-xs text-slate-400">Completion: {client.completion_percent}%</span>
                      {client.created_at && (
                        <span className="text-xs text-slate-400">
                          {new Date(client.created_at).toLocaleDateString('en-GB')}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/wizard/${client.session_token}`)}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    {currentIdx < STATUS_FLOW.length - 1 && (
                      <Button
                        size="sm"
                        onClick={() => updateStatus(client.session_token, STATUS_FLOW[currentIdx + 1])}
                      >
                        → {STATUS_CONFIG[STATUS_FLOW[currentIdx + 1]].label}
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
