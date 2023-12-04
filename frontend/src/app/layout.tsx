import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ReactNode } from 'react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DRFTR',
  description: 'Responses drafted for your Gmail inbox',
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {

	const classes = [
		inter.className,
		'h-full',
		'ml-[33%]',
		'flex',
		'items-center'
	]

	return (
	  	<html lang="en" className='h-full'>
		    <body className={classes.join(' ')}>
				{children}
			</body>
	    </html>
	)
}
