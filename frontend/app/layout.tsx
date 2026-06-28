'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '../src/lib/queryClient'
import './globals.css'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <title>Tally Sync Platform</title>
        <meta name="description" content="Cloud dashboard for Tally ERP synchronisation" />
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </body>
    </html>
  )
}
