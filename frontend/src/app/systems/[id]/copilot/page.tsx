'use client'

import { useState, useRef, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Sparkles, Send, Loader2, Bot, User, BookOpen, RefreshCw } from 'lucide-react'
import { assistantApi, tfApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/use-toast'
import type { QAResult } from '@/types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: QAResult['citations']
}

const STARTER_QUESTIONS = [
  'What is the intended purpose of this AI system?',
  'What human oversight mechanisms are in place?',
  'What are the known performance limitations?',
  'Which risks have been identified and mitigated?',
  'How is user data protected under GDPR?',
]

export default function CopilotPage() {
  const { id } = useParams<{ id: string }>()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isIndexed, setIsIndexed] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: revisions } = useQuery({
    queryKey: ['revisions', id],
    queryFn: () => tfApi.listRevisions(id).then((r) => r.data),
  })
  const currentRevision = revisions?.[0]

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const indexMutation = useMutation({
    mutationFn: () =>
      assistantApi.indexRevision(id, currentRevision?.id).then((r) => r.data),
    onSuccess: (data) => {
      setIsIndexed(true)
      toast({ title: `Indexed ${data.indexed_sections} sections for Q&A` })
    },
    onError: () =>
      toast({ variant: 'destructive', title: 'Indexing failed. Please try again.' }),
  })

  const qaMutation = useMutation({
    mutationFn: (question: string) =>
      assistantApi.qa(id, question, currentRevision?.id).then((r) => r.data),
    onSuccess: (data, question) => {
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: data.answer,
          citations: data.citations,
        },
      ])
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I could not answer that question. Please try again.',
        },
      ])
    },
  })

  function handleSend(question?: string) {
    const q = question ?? input.trim()
    if (!q) return

    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: 'user', content: q },
    ])
    setInput('')
    qaMutation.mutate(q)
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold">AI Copilot — Q&A</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Ask questions about this system&apos;s Technical File. The AI answers based on the
          content you&apos;ve filled in.
        </p>
      </div>

      {/* Index step */}
      {!isIndexed && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="flex items-center justify-between py-4 gap-4">
            <div className="space-y-0.5">
              <p className="text-sm font-medium">Index Technical File for Q&A</p>
              <p className="text-xs text-muted-foreground">
                Build the knowledge base from your current revision so the AI can answer
                questions accurately.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => indexMutation.mutate()}
              disabled={indexMutation.isPending || !currentRevision}
              className="shrink-0"
            >
              {indexMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : (
                <BookOpen className="h-4 w-4 mr-1" />
              )}
              {indexMutation.isPending ? 'Indexing…' : 'Build index'}
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Chat area */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="flex flex-col h-[560px]">
            {/* Message list */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-3">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Ask anything about this Technical File</p>
                    <p className="text-sm text-muted-foreground">
                      {isIndexed
                        ? 'Type your question below or choose a starter question →'
                        : 'Build the index first, then start asking questions'}
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm space-y-2 ${
                        msg.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1 border-t border-muted-foreground/20">
                          {msg.citations.map((c) => (
                            <Badge key={c.section_number} variant="outline" className="text-xs">
                              §{c.section_number} {c.section_name}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    {msg.role === 'user' && (
                      <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center shrink-0 mt-0.5">
                        <User className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                  </div>
                ))
              )}
              {qaMutation.isPending && (
                <div className="flex gap-3 justify-start">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                  <div className="bg-muted rounded-lg px-4 py-2.5 text-sm">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input bar */}
            <div className="border-t p-4 flex gap-2">
              <Input
                placeholder={
                  isIndexed
                    ? 'Ask a question about this Technical File…'
                    : 'Build the index first to enable Q&A'
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                disabled={!isIndexed || qaMutation.isPending}
              />
              <Button
                onClick={() => handleSend()}
                disabled={!input.trim() || !isIndexed || qaMutation.isPending}
                size="icon"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </Card>

          {/* Re-index */}
          {isIndexed && (
            <div className="flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-muted-foreground"
                onClick={() => indexMutation.mutate()}
                disabled={indexMutation.isPending}
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Re-index
              </Button>
            </div>
          )}
        </div>

        {/* Starter questions */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Suggested questions
          </p>
          {STARTER_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => handleSend(q)}
              disabled={!isIndexed || qaMutation.isPending}
              className="w-full text-left text-sm p-3 rounded-md border hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
