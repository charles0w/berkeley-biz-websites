'use client'
import { useState, useEffect } from 'react'

export default function StickyFAB({ phone }: { phone: string }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const handler = () => setVisible(window.scrollY > 380)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3 pointer-events-none'
      }`}
    >
      <a
        href={`tel:${phone}`}
        className="flex items-center gap-2.5 bg-stone-900 text-stone-50 px-7 py-3.5 shadow-ambient-lg text-sm font-sans font-medium tracking-wide hover:bg-stone-800 active:bg-stone-700 transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
          <path d="M13 10.33v1.84a1.22 1.22 0 0 1-1.33 1.22 12.1 12.1 0 0 1-5.28-1.88 11.93 11.93 0 0 1-3.67-3.67A12.1 12.1 0 0 1 .84 2.47 1.22 1.22 0 0 1 2.05 1.1h1.84c.6 0 1.11.44 1.2 1.03.08.56.22 1.1.42 1.62a1.22 1.22 0 0 1-.27 1.29L4.4 5.88a9.74 9.74 0 0 0 3.67 3.67l.84-.84a1.22 1.22 0 0 1 1.29-.28c.52.2 1.06.34 1.62.42.6.09 1.04.61 1.18 1.48z" fill="currentColor"/>
        </svg>
        Call us
      </a>
    </div>
  )
}
