'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from '@/components/ui/use-toast'
import { integrationApi } from '@/lib/api'

// Credential field definitions per integration type
const INTEGRATION_TYPES = [
  { value: 'github', label: 'GitHub', credFields: ['token'], configFields: ['owner', 'repo'] },
  {
    value: 'gitlab',
    label: 'GitLab',
    credFields: ['token'],
    configFields: ['base_url', 'project_id'],
  },
  {
    value: 'mlflow',
    label: 'MLflow',
    credFields: ['username', 'password'],
    configFields: ['base_url', 'experiment_ids'],
  },
  {
    value: 'wandb',
    label: 'Weights & Biases',
    credFields: ['api_key'],
    configFields: ['entity', 'project'],
  },
  {
    value: 'webhook',
    label: 'Webhook',
    credFields: ['webhook_secret'],
    configFields: [],
  },
  {
    value: 'ci_cd',
    label: 'CI/CD (Generic)',
    credFields: ['webhook_secret'],
    configFields: [],
  },
]

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  type: z.string().min(1, 'Type is required'),
  // Credential fields (all optional at schema level; validated per type)
  token: z.string().optional(),
  api_key: z.string().optional(),
  username: z.string().optional(),
  password: z.string().optional(),
  webhook_secret: z.string().optional(),
  // Config fields
  base_url: z.string().optional(),
  owner: z.string().optional(),
  repo: z.string().optional(),
  project_id: z.string().optional(),
  entity: z.string().optional(),
  project: z.string().optional(),
  experiment_ids: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

const FIELD_LABELS: Record<string, string> = {
  token: 'Personal Access Token',
  api_key: 'API Key',
  username: 'Username',
  password: 'Password',
  webhook_secret: 'Webhook Secret',
  base_url: 'Base URL',
  owner: 'Owner (user or org)',
  repo: 'Repository name',
  project_id: 'Project ID',
  entity: 'Entity (team)',
  project: 'Project name',
  experiment_ids: 'Experiment IDs (comma-separated)',
}

const FIELD_PLACEHOLDERS: Record<string, string> = {
  token: 'ghp_...',
  api_key: 'wandb_...',
  base_url: 'http://localhost:5000',
  owner: 'my-org',
  repo: 'my-model-repo',
  project_id: '12345',
  entity: 'my-team',
  project: 'my-project',
  experiment_ids: '0,1',
  webhook_secret: 'my-secret-token',
}

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  orgId: string
  onCreated: () => void
}

export function ConnectDialog({ open, onOpenChange, orgId, onCreated }: Props) {
  const [selectedType, setSelectedType] = useState('')
  const typeInfo = INTEGRATION_TYPES.find((t) => t.value === selectedType)

  const { register, handleSubmit, setValue, reset, formState: { errors } } =
    useForm<FormValues>({ resolver: zodResolver(schema) })

  const createMutation = useMutation({
    mutationFn: (values: FormValues) => {
      const credFields = typeInfo?.credFields ?? []
      const configFieldNames = typeInfo?.configFields ?? []

      const credentials: Record<string, string> = {}
      const config: Record<string, string> = {}

      for (const f of credFields) {
        const val = (values as Record<string, string | undefined>)[f]
        if (val) credentials[f] = val
      }
      for (const f of configFieldNames) {
        const val = (values as Record<string, string | undefined>)[f]
        if (val) config[f] = val
      }

      return integrationApi.create(orgId, {
        name: values.name,
        type: values.type,
        credentials: Object.keys(credentials).length ? credentials : undefined,
        config: Object.keys(config).length ? config : undefined,
      })
    },
    onSuccess: () => {
      toast({ title: 'Integration added' })
      reset()
      setSelectedType('')
      onCreated()
    },
    onError: () => toast({ variant: 'destructive', title: 'Failed to add integration' }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Integration</DialogTitle>
          <DialogDescription>
            Connect a Git repository or MLOps platform to sync metadata into your Annex IV
            documentation.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit((v) => createMutation.mutate(v))}
          className="space-y-4 mt-2"
        >
          {/* Name */}
          <div className="space-y-1">
            <label className="text-sm font-medium">
              Name <span className="text-destructive">*</span>
            </label>
            <Input {...register('name')} placeholder="My GitHub integration" />
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>

          {/* Type selector */}
          <div className="space-y-1">
            <label className="text-sm font-medium">
              Type <span className="text-destructive">*</span>
            </label>
            <Select
              onValueChange={(v) => {
                setSelectedType(v)
                setValue('type', v)
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select integration type" />
              </SelectTrigger>
              <SelectContent>
                {INTEGRATION_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Dynamic credential fields */}
          {typeInfo?.credFields.map((field) => (
            <div key={field} className="space-y-1">
              <label className="text-sm font-medium">{FIELD_LABELS[field] ?? field}</label>
              <Input
                {...register(field as keyof FormValues)}
                type={['token', 'api_key', 'password', 'webhook_secret'].includes(field) ? 'password' : 'text'}
                placeholder={FIELD_PLACEHOLDERS[field] ?? ''}
              />
            </div>
          ))}

          {/* Dynamic config fields */}
          {typeInfo?.configFields.map((field) => (
            <div key={field} className="space-y-1">
              <label className="text-sm font-medium text-muted-foreground">
                {FIELD_LABELS[field] ?? field}{' '}
                <span className="text-xs">(optional)</span>
              </label>
              <Input
                {...register(field as keyof FormValues)}
                placeholder={FIELD_PLACEHOLDERS[field] ?? ''}
              />
            </div>
          ))}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending || !selectedType}>
              {createMutation.isPending ? 'Adding…' : 'Add integration'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
