'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AlertTriangle, CheckCircle } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { systemApi } from '@/lib/api'
import { useAuthStore } from '@/lib/auth'
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/use-toast'
import type { IntendedPurposeResult } from '@/types'

const schema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  description: z.string().optional(),
  intended_purpose: z.string().optional(),
  category: z.enum(['high_risk', 'limited_risk', 'minimal_risk']),
})

type FormValues = z.infer<typeof schema>

export default function NewSystemPage() {
  const router = useRouter()
  const currentOrg = useAuthStore((s) => s.currentOrg)
  const [purposeResult, setPurposeResult] = useState<IntendedPurposeResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { category: 'high_risk' },
  })

  const intentedPurposeValue = watch('intended_purpose')

  const createMutation = useMutation({
    mutationFn: (values: FormValues) =>
      systemApi.create({
        org_id: currentOrg!.id,
        name: values.name,
        description: values.description,
        intended_purpose: values.intended_purpose,
        category: values.category,
        annex_iii_classification: values.category === 'high_risk',
      }),
    onSuccess: (res) => {
      toast({ title: 'AI system created', description: `"${res.data.name}" has been added.` })
      router.push(`/systems/${res.data.id}/annex-iv`)
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to create AI system.' })
    },
  })

  async function validatePurpose() {
    if (!intentedPurposeValue) return
    setIsValidating(true)
    try {
      const res = await systemApi.validatePurpose(intentedPurposeValue)
      setPurposeResult(res.data)
    } catch {
      toast({ variant: 'destructive', title: 'Validation failed' })
    } finally {
      setIsValidating(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Add AI System</h1>
        <p className="text-muted-foreground text-sm">
          Register a new AI system for EU AI Act compliance tracking.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System details</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit((v) => createMutation.mutate(v))}
            className="space-y-5"
          >
            <div className="space-y-1">
              <label className="text-sm font-medium">
                Name <span className="text-destructive">*</span>
              </label>
              <Input placeholder="e.g. Credit Scoring Model v2" {...register('name')} />
              {errors.name && (
                <p className="text-xs text-destructive">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">Description</label>
              <Textarea
                placeholder="Brief description of the system…"
                rows={3}
                {...register('description')}
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">Intended Purpose</label>
              <Textarea
                placeholder="Describe what this AI system is designed to do…"
                rows={4}
                {...register('intended_purpose')}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={validatePurpose}
                disabled={isValidating || !intentedPurposeValue}
              >
                {isValidating ? 'Validating…' : 'Validate against Annex III'}
              </Button>

              {purposeResult && (
                <div
                  className={`mt-2 p-3 rounded-md border text-sm space-y-2 ${
                    purposeResult.is_high_risk
                      ? 'border-amber-300 bg-amber-50'
                      : 'border-green-300 bg-green-50'
                  }`}
                >
                  <div className="flex items-center gap-2 font-medium">
                    {purposeResult.is_high_risk ? (
                      <>
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        <span className="text-amber-800">High-risk indicators detected</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span className="text-green-800">No high-risk indicators detected</span>
                      </>
                    )}
                  </div>
                  {purposeResult.triggers.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {purposeResult.triggers.map((t) => (
                        <Badge key={t} variant="destructive" className="text-xs">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {purposeResult.warnings.map((w, i) => (
                    <p key={i} className="text-amber-700 text-xs">
                      {w}
                    </p>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">
                Risk Category <span className="text-destructive">*</span>
              </label>
              <Select
                defaultValue="high_risk"
                onValueChange={(v) =>
                  setValue('category', v as FormValues['category'])
                }
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
              {errors.category && (
                <p className="text-xs text-destructive">{errors.category.message}</p>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating…' : 'Create system'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
