'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Link as LinkIcon } from 'lucide-react'
import { evidenceApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/use-toast'

interface EvidenceUploadProps {
  revisionId: string
  sectionId?: string
  onUploaded?: () => void
}

export function EvidenceUpload({ revisionId, sectionId, onUploaded }: EvidenceUploadProps) {
  const [tab, setTab] = useState<'file' | 'url'>('file')
  const [urlValue, setUrlValue] = useState('')
  const [source, setSource] = useState('')
  const [version, setVersion] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    multiple: false,
  })

  async function handleFileUpload() {
    if (!acceptedFiles.length) return
    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', acceptedFiles[0])
    formData.append('revision_id', revisionId)
    if (sectionId) formData.append('section_id', sectionId)
    if (source) formData.append('source', source)
    if (version) formData.append('version', version)
    try {
      await evidenceApi.upload(formData)
      toast({ title: 'Evidence uploaded' })
      onUploaded?.()
    } catch {
      toast({ variant: 'destructive', title: 'Upload failed' })
    } finally {
      setIsUploading(false)
    }
  }

  async function handleUrlSubmit() {
    if (!urlValue) return
    setIsUploading(true)
    try {
      await evidenceApi.addUrl({
        revision_id: revisionId,
        url: urlValue,
        source: source || undefined,
        version: version || undefined,
      })
      toast({ title: 'Evidence URL added' })
      setUrlValue('')
      onUploaded?.()
    } catch {
      toast({ variant: 'destructive', title: 'Failed to add URL' })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-3">
      {/* Tab selector */}
      <div className="flex gap-1 text-xs border rounded-md p-1 w-fit">
        {(['file', 'url'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              'px-3 py-1 rounded transition-colors capitalize',
              tab === t ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
            )}
          >
            {t === 'file' ? 'File' : 'URL'}
          </button>
        ))}
      </div>

      {tab === 'file' ? (
        <div className="space-y-3">
          <div
            {...getRootProps()}
            className={cn(
              'border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-colors text-sm',
              isDragActive ? 'border-primary bg-primary/5' : 'border-muted hover:border-primary/50'
            )}
          >
            <input {...getInputProps()} />
            <Upload className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
            {isDragActive ? (
              <p>Drop the file here…</p>
            ) : acceptedFiles.length ? (
              <p className="font-medium">{acceptedFiles[0].name}</p>
            ) : (
              <p className="text-muted-foreground">Drag & drop or click to select</p>
            )}
          </div>
          <Input placeholder="Source (optional)" value={source} onChange={(e) => setSource(e.target.value)} />
          <Input placeholder="Version (optional)" value={version} onChange={(e) => setVersion(e.target.value)} />
          <Button
            size="sm"
            className="w-full"
            onClick={handleFileUpload}
            disabled={!acceptedFiles.length || isUploading}
          >
            {isUploading ? 'Uploading…' : 'Upload file'}
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="relative">
            <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="https://…"
              value={urlValue}
              onChange={(e) => setUrlValue(e.target.value)}
              className="pl-9"
            />
          </div>
          <Input placeholder="Source (optional)" value={source} onChange={(e) => setSource(e.target.value)} />
          <Input placeholder="Version (optional)" value={version} onChange={(e) => setVersion(e.target.value)} />
          <Button
            size="sm"
            className="w-full"
            onClick={handleUrlSubmit}
            disabled={!urlValue || isUploading}
          >
            {isUploading ? 'Adding…' : 'Add URL'}
          </Button>
        </div>
      )}
    </div>
  )
}
