'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AlertTriangle } from 'lucide-react'
import { systemApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { toast } from '@/components/ui/use-toast'
import type { AISystemCategory } from '@/types'

const schema = z.object({
  name: z.string().min(2),
  description: z.string().optional(),
  intended_purpose: z.string().optional(),
  category: z.enum(['high_risk', 'limited_risk', 'minimal_risk']),
})

type FormValues = z.infer<typeof schema>

export default function SystemSettingsPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const { data: system, isLoading } = useQuery({
    queryKey: ['system', id],
    queryFn: () => systemApi.get(id).then((r) => r.data),
  })

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: system
      ? {
          name: system.name,
          description: system.description ?? '',
          intended_purpose: system.intended_purpose ?? '',
          category: system.category,
        }
      : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: (values: FormValues) => systemApi.update(id, values),
    onSuccess: () => toast({ title: 'Settings saved' }),
    onError: () => toast({ variant: 'destructive', title: 'Save failed' }),
  })

  const archiveMutation = useMutation({
    mutationFn: () => systemApi.update(id, { status: 'archived' }),
    onSuccess: () => {
      toast({ title: 'System archived' })
      router.push('/dashboard')
    },
    onError: () => toast({ variant: 'destructive', title: 'Archive failed' }),
  })

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse max-w-2xl">
        <div className="h-8 bg-muted rounded w-48" />
        <div className="h-40 bg-muted rounded" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-8">
      <h2 className="text-xl font-semibold">System Settings</h2>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">General</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit((v) => updateMutation.mutate(v))}
            className="space-y-5"
          >
            <div className="space-y-1">
              <label className="text-sm font-medium">
                Name <span className="text-destructive">*</span>
              </label>
              <Input {...register('name')} />
              {errors.name && (
                <p className="text-xs text-destructive">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">Description</label>
              <Textarea rows={3} {...register('description')} />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">Intended Purpose</label>
              <Textarea rows={4} {...register('intended_purpose')} />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">Risk Category</label>
              <Select
                defaultValue={system?.category}
                onValueChange={(v) => setValue('category', v as AISystemCategory)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="high_risk">High Risk (Annex III)</SelectItem>
                  <SelectItem value="limited_risk">Limited Risk</SelectItem>
                  <SelectItem value="minimal_risk">Minimal Risk</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving…' : 'Save changes'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Danger zone */}
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-base text-destructive flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Danger Zone
          </CardTitle>
          <CardDescription>Irreversible actions — proceed with caution.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Archive this system</p>
              <p className="text-xs text-muted-foreground">
                The system will be hidden from your dashboard but data is preserved.
              </p>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                if (confirm('Archive this AI system? It will no longer appear on the dashboard.')) {
                  archiveMutation.mutate()
                }
              }}
              disabled={archiveMutation.isPending}
            >
              Archive
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
