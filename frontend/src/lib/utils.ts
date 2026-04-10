import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, parseISO } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy')
  } catch {
    return dateStr
  }
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function getCompletenessColor(score: number): string {
  if (score >= 0.66) return 'text-green-600'
  if (score >= 0.33) return 'text-yellow-600'
  return 'text-red-600'
}

export function getCompletenessBarColor(score: number): string {
  if (score >= 0.66) return 'bg-green-500'
  if (score >= 0.33) return 'bg-yellow-500'
  return 'bg-red-500'
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function truncate(str: string, max: number): string {
  if (str.length <= max) return str
  return str.slice(0, max) + '...'
}
