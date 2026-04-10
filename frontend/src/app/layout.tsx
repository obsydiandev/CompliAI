import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/lib/providers'
import { Toaster } from '@/components/ui/toaster'

export const metadata: Metadata = {
  title: 'CompliAI — EU AI Act Compliance',
  description: 'Automate your EU AI Act Annex IV Technical File lifecycle management',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}
