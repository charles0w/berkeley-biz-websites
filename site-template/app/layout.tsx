import type { Metadata } from 'next'
import { Plus_Jakarta_Sans, Newsreader, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import business from '../business.json'

const jakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-jakarta',
  weight: ['300', '400', '500', '600'],
  display: 'swap',
})

const newsreader = Newsreader({
  subsets: ['latin'],
  variable: '--font-newsreader',
  style: ['normal', 'italic'],
  weight: ['300', '400', '500'],
  display: 'swap',
  adjustFontFallback: false,
})

const mono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: business.name,
  description: business.tagline,
  openGraph: {
    title: business.name,
    description: business.tagline,
    images: business.photos[0] ? [{ url: `/${business.photos[0]}` }] : [],
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${jakarta.variable} ${newsreader.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
