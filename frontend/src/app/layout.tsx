import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DRFTR',
  description: 'Responses drafted for your Gmail inbox',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
	  <ClerkProvider>
	  	<html lang="en">
		    <body className={inter.className}>{children}</body>
	    </html>
	  </ClerkProvider>
  )
}