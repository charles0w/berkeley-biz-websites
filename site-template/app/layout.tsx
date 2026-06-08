import type { Metadata } from 'next'
import {
  Plus_Jakarta_Sans,
  Amatic_SC,
  Playfair_Display,
  Space_Grotesk,
  DM_Serif_Display,
  JetBrains_Mono,
} from 'next/font/google'
import './globals.css'
import business from '../business.json'

// Body font — used across all themes
const jakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-jakarta',
  weight: ['300', '400', '500', '600'],
  display: 'swap',
})

// Monospace labels
const mono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400'],
  display: 'swap',
})

// Display fonts — each assigned to a CSS var; themes.ts picks the right one
const artisan = Amatic_SC({
  subsets: ['latin'],
  variable: '--font-artisan',   // cafe, food, gelato
  weight: ['400', '700'],
  display: 'swap',
})

const elegant = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-elegant',   // salon, beauty, nail
  weight: ['400', '500', '700'],
  style: ['normal', 'italic'],
  display: 'swap',
})

const grotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-grotesk',   // fitness, services
  weight: ['400', '500', '700'],
  display: 'swap',
})

const serif = DM_Serif_Display({
  subsets: ['latin'],
  variable: '--font-serif',     // retail, restaurant
  weight: ['400'],
  style: ['normal', 'italic'],
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
  const fontVars = [
    jakarta.variable,
    mono.variable,
    artisan.variable,
    elegant.variable,
    grotesk.variable,
    serif.variable,
  ].join(' ')

  return (
    <html lang="en" className={fontVars}>
      <body>{children}</body>
    </html>
  )
}
