'use client'
import { useState, useRef, useEffect } from 'react'
import type { Theme } from '../themes'

type Service = { name: string; price: string }

type Props = {
  name: string
  phone: string
  address: string
  hours: Record<string, string>
  services: Service[]
  category: string
  theme: Theme
}

type Message = {
  role: 'bot' | 'user'
  text: string
}

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

function formatHours(hours: Record<string, string>): string {
  const entries = Object.entries(hours)
  if (entries.length === 0) return 'Hours not listed — call us to confirm.'
  return entries.map(([d, h]) => `${d.slice(0, 3)}: ${h}`).join(' · ')
}

function todayHours(hours: Record<string, string>): string {
  const today = DAY_NAMES[new Date().getDay()]
  return hours[today] ? `Today (${today}): ${hours[today]}` : 'Closed today'
}

const CATEGORY_QUESTIONS: Record<string, { q: string; a: (p: Props) => string }[]> = {
  cafe: [
    { q: '☕ What do you serve?', a: (p) => p.services.length > 0 ? `We offer ${p.services.slice(0, 4).map(s => s.name).join(', ')}, and more. Prices start from ${p.services[0]?.price}.` : 'Coffee, espresso drinks, and fresh pastries daily.' },
    { q: '📅 Do you take reservations?', a: () => "We're walk-in friendly — no reservation needed. Come by anytime we're open." },
  ],
  restaurant: [
    { q: '🍽 Do you take reservations?', a: (p) => `Call us at ${p.phone} to reserve a table. Walk-ins welcome when space allows.` },
    { q: "📋 What's on the menu?", a: (p) => p.services.length > 0 ? `Our menu includes ${p.services.slice(0, 4).map(s => s.name).join(', ')}. Prices start from ${p.services[0]?.price}.` : "Ask us about today's specials when you call." },
  ],
  salon: [
    { q: '✂️ Do you take walk-ins?', a: (p) => `We take walk-ins when space allows. To guarantee your spot, call ${p.phone} to book ahead.` },
    { q: '💇 What services do you offer?', a: (p) => p.services.length > 0 ? `We offer ${p.services.slice(0, 4).map(s => `${s.name} (${s.price})`).join(', ')}, and more.` : 'Cuts, color, blowouts, and treatments. Call for our full menu.' },
  ],
  beauty: [
    { q: '💅 Do I need an appointment?', a: (p) => `Appointments are recommended. Call ${p.phone} or walk in — we'll fit you in when we can.` },
    { q: '🌸 What services do you offer?', a: (p) => p.services.length > 0 ? `We offer ${p.services.slice(0, 4).map(s => `${s.name} (${s.price})`).join(', ')}, and more.` : 'Manicures, pedicures, gel nails, nail art, and more. Call for full menu.' },
  ],
  fitness: [
    { q: '🏋️ Do you offer drop-in classes?', a: (p) => p.services.find(s => s.name.toLowerCase().includes('drop')) ? `Yes — drop-in classes are available. Check our schedule or call ${p.phone}.` : `Call ${p.phone} for class schedules and drop-in rates.` },
    { q: '💪 What classes do you have?', a: (p) => p.services.length > 0 ? `We offer ${p.services.slice(0, 4).map(s => s.name).join(', ')}, and more.` : 'Group classes, personal training, and open gym. Call for current schedule.' },
  ],
  retail: [
    { q: '🛍 What do you carry?', a: (p) => p.services.length > 0 ? `We carry a curated selection. ${p.services.slice(0, 3).map(s => s.name).join(', ')}, and more — come in to browse.` : 'Stop in to browse our full selection. New arrivals every week.' },
    { q: '🎁 Do you offer gift wrapping?', a: () => "Yes — we're happy to gift wrap your purchase in store." },
  ],
  services: [
    { q: '📋 Do you offer free consultations?', a: (p) => `Yes. Call ${p.phone} or stop by to discuss your needs. No obligation.` },
    { q: '💼 What services do you offer?', a: (p) => p.services.length > 0 ? `We offer ${p.services.slice(0, 4).map(s => `${s.name} (${s.price})`).join(', ')}, and more.` : 'Call us to discuss your specific needs and get a quote.' },
  ],
}

export default function AIFaqChat({ name, phone, address, hours, services, category, theme }: Props) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [typing, setTyping] = useState(false)
  const [started, setStarted] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const catKey = (['cafe', 'restaurant', 'salon', 'beauty', 'fitness', 'retail'] as const)
    .find(k => category?.toLowerCase().includes(k)) ?? 'services'
  const questions = CATEGORY_QUESTIONS[catKey] ?? CATEGORY_QUESTIONS.services

  const universalQuestions = [
    { q: '🕐 When are you open?', a: () => `${todayHours(hours)}\n\nFull hours:\n${formatHours(hours)}` },
    { q: '📍 Where are you located?', a: () => `We're at ${address}. Find us on Google Maps for directions.` },
    { q: '📞 How do I contact you?', a: () => phone ? `Call or text us at ${phone}. We're happy to help!` : "Stop by during business hours — we'd love to meet you." },
  ]

  const allQuestions = [...universalQuestions, ...questions]

  function openChat() {
    setOpen(true)
    if (!started) {
      setStarted(true)
      setTyping(true)
      setTimeout(() => {
        setTyping(false)
        setMessages([{ role: 'bot', text: `Hi, welcome to ${name}! How can I help you today?` }])
      }, 800)
    }
  }

  function handleQuestion(q: string, a: string) {
    const answer = a.replace(/\n/g, '\n')
    setMessages(prev => [...prev, { role: 'user', text: q }, { role: 'bot', text: '…' }])
    setTyping(true)
    setTimeout(() => {
      setTyping(false)
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'bot', text: answer },
      ])
    }, 700)
  }

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, typing])

  return (
    <>
      {/* Floating bubble */}
      <button
        onClick={() => open ? setOpen(false) : openChat()}
        className="fixed bottom-24 right-5 z-40 w-13 h-13 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105 active:scale-95"
        style={{ background: theme.primary, width: 52, height: 52 }}
        aria-label="Chat with us"
      >
        {open ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        )}
      </button>

      {/* Chat window */}
      {open && (
        <div
          className="fixed bottom-[88px] right-4 z-50 w-[min(360px,calc(100vw-2rem))] rounded-2xl shadow-2xl flex flex-col overflow-hidden"
          style={{ background: theme.bg, border: `1px solid ${theme.border}`, maxHeight: '70vh' }}
        >
          {/* Header */}
          <div
            className="flex items-center gap-3 px-4 py-3 shrink-0"
            style={{ background: theme.primary }}
          >
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <div>
              <p className="font-sans text-sm font-semibold text-white leading-tight">{name}</p>
              <p className="font-mono text-[10px] text-white/70">Ask us anything</p>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3" style={{ minHeight: 140 }}>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} chat-bubble-in`}
              >
                <div
                  className="max-w-[85%] px-3 py-2 rounded-xl font-sans text-sm leading-relaxed whitespace-pre-line"
                  style={
                    msg.role === 'user'
                      ? { background: theme.primary, color: 'white' }
                      : { background: theme.dark ? 'rgba(255,255,255,0.07)' : theme.border + 'aa', color: theme.fore }
                  }
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {typing && (
              <div className="flex justify-start chat-bubble-in">
                <div
                  className="px-3 py-2.5 rounded-xl flex gap-1 items-center"
                  style={{ background: theme.dark ? 'rgba(255,255,255,0.07)' : theme.border + 'aa' }}
                >
                  {[0, 1, 2].map(i => (
                    <span
                      key={i}
                      className="typing-dot inline-block w-1.5 h-1.5 rounded-full"
                      style={{ background: theme.foreSecondary }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick replies */}
          <div
            className="px-3 pb-3 pt-2 flex flex-wrap gap-1.5 shrink-0"
            style={{ borderTop: `1px solid ${theme.border}` }}
          >
            {allQuestions.map(({ q, a }, i) => (
              <button
                key={i}
                onClick={() => handleQuestion(q, a({ name, phone, address, hours, services, category, theme }))}
                className="font-sans text-xs px-3 py-1.5 rounded-full border transition-colors"
                style={{
                  borderColor: theme.border,
                  color: theme.fore,
                  background: 'transparent',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = theme.border)}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
