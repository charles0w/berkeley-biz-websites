import business from '../business.json'
import { getTheme, heroOverlay, noPhotoGradient } from '../themes'
import ServicesSection from '../components/ServicesSection'
import ReviewsCard from '../components/ReviewsCard'
import AIFaqChat from '../components/AIFaqChat'
import StickyFAB from '../components/StickyFAB'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const DAY_SHORT: Record<string, string> = {
  Monday: 'Mon', Tuesday: 'Tue', Wednesday: 'Wed', Thursday: 'Thu',
  Friday: 'Fri', Saturday: 'Sat', Sunday: 'Sun',
}

// Typed access to generated fields
const biz = business as typeof business & {
  plan: 'basic' | 'pro'
  variant: number
  about: string
  tagline: string
  services: Array<{ name: string; price: string }>
}

function Stars({ rating, color }: { rating: number; color: string }) {
  const full = Math.floor(rating)
  const half = rating - full >= 0.5
  return (
    <span className="inline-flex gap-0.5" aria-label={`${rating} stars`}>
      {Array.from({ length: 5 }, (_, i) => (
        <svg key={i} width="14" height="14" viewBox="0 0 12 12" fill="none">
          <path
            d="M6 1l1.35 2.74L10.5 4.27l-2.25 2.19.53 3.09L6 8.02 3.22 9.55l.53-3.09L1.5 4.27l3.15-.53L6 1z"
            fill={color}
            stroke={color}
            strokeWidth="0.75"
            opacity={i < full || (half && i === full) ? 1 : 0.15}
          />
        </svg>
      ))}
    </span>
  )
}

export default function Page() {
  const theme = getTheme(biz.category)
  const isPro = biz.plan === 'pro'
  const variant = (biz.variant ?? 0) % 4

  const photos = (biz.photos ?? []) as string[]
  const heroPhoto = photos[0]
  const galleryPhotos = photos.slice(0, 8)
  const hours = (biz.hours ?? {}) as Record<string, string>
  const orderedDays = DAYS.filter(d => d in hours)
  const hasHours = orderedDays.length > 0
  const hasAbout = Boolean(biz.about?.trim())
  const services = (biz.services ?? []) as Array<{ name: string; price: string }>

  const streetLine = biz.address.split(',')[0]?.trim() ?? ''
  const cityLine = biz.address.split(',').slice(1).join(',').trim()
  const mapsUrl = `https://maps.google.com/?q=${encodeURIComponent(biz.address)}`

  // Today's day for hours highlight
  const todayIdx = new Date().getDay()
  const today = DAYS[todayIdx === 0 ? 6 : todayIdx - 1]

  // Variant-driven hero sizing
  const heroNameSize = [
    'clamp(3.5rem, 9vw, 7rem)',    // v0: standard
    'clamp(4rem, 10.5vw, 8.5rem)', // v1: large
    'clamp(3rem, 7.5vw, 5.5rem)',  // v2: compact + centred
    'clamp(3.5rem, 9vw, 7rem)',    // v3: standard with inline rating
  ][variant]

  const heroCentered = variant === 2
  const showRatingInline = variant === 3

  // Services label varies by category
  const servicesLabel = {
    cafe: 'Menu',
    food: 'Menu',
    restaurant: 'Menu',
    salon: 'Services & Pricing',
    beauty: 'Services & Pricing',
    nail: 'Services & Pricing',
    fitness: 'Classes & Rates',
    retail: 'What We Carry',
    services: 'Services',
  }[biz.category] ?? 'Services'

  return (
    <main
      className="min-h-[100dvh] font-sans theme-root"
      style={{
        background: theme.bg,
        color: theme.fore,
        ['--font-display' as string]: `var(${theme.fontVar})`,
        ['--theme-primary' as string]: theme.primary,
        ['--theme-border' as string]: theme.border,
        ['--theme-fore' as string]: theme.fore,
        ['--theme-fore-secondary' as string]: theme.foreSecondary,
      } as React.CSSProperties}
    >

      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="relative min-h-[100svh] flex flex-col overflow-hidden">
        {heroPhoto ? (
          <img
            src={`/${heroPhoto}`}
            alt={biz.name}
            className="absolute inset-0 w-full h-full object-cover photo-warm"
          />
        ) : (
          <div
            className="absolute inset-0"
            style={{ background: noPhotoGradient(biz.category) }}
          />
        )}

        {/* Gradient overlay */}
        <div
          className="absolute inset-0"
          style={{ background: heroOverlay(theme) }}
        />

        {/* Top bar */}
        <div className="relative z-10 flex items-center justify-between px-6 pt-7 md:px-12">
          <span
            className="font-mono text-[10px] tracking-[0.2em] uppercase"
            style={{ color: theme.labelColor }}
          >
            {cityLine || 'Berkeley, CA'}
          </span>
          {biz.phone && (
            <a
              href={`tel:${biz.phone}`}
              className="font-mono text-[11px] tracking-wider transition-opacity hover:opacity-100"
              style={{ color: theme.labelColor, opacity: 0.85 }}
            >
              {biz.phone}
            </a>
          )}
        </div>

        {/* Hero content */}
        <div
          className={`relative z-10 mt-auto px-6 pb-14 md:px-12 md:pb-20 ${heroCentered ? 'text-center mx-auto w-full' : 'max-w-4xl'}`}
        >
          {/* Rating — default position (not variant 3) */}
          {biz.rating > 0 && !showRatingInline && (
            <div
              className={`inline-flex items-center gap-2 mb-5 px-3 py-1.5 rounded-full ${heroCentered ? 'mx-auto' : ''}`}
              style={{
                background: theme.dark ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.8)',
                border: `1px solid ${theme.border}`,
              }}
            >
              <Stars rating={biz.rating} color={theme.primary} />
              <span className="font-mono text-[11px]" style={{ color: theme.labelColor }}>
                {biz.rating} · {biz.review_count.toLocaleString()} reviews
              </span>
            </div>
          )}

          {/* Variant 1: tagline above name */}
          {variant === 1 && biz.tagline && (
            <p
              className="font-sans font-light text-sm tracking-widest uppercase mb-3"
              style={{ color: theme.foreSecondary }}
            >
              {biz.tagline}
            </p>
          )}

          {/* Name + inline rating (variant 3) */}
          <div className={`flex ${showRatingInline ? 'items-end gap-4 flex-wrap' : ''}`}>
            <h1
              className="font-display font-bold leading-[0.92] tracking-tight text-balance"
              style={{ fontSize: heroNameSize, color: theme.fore }}
            >
              {biz.name}
            </h1>
            {showRatingInline && biz.rating > 0 && (
              <div
                className="inline-flex items-center gap-1.5 mb-2 px-2.5 py-1 rounded-full shrink-0"
                style={{
                  background: theme.dark ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.8)',
                  border: `1px solid ${theme.border}`,
                }}
              >
                <Stars rating={biz.rating} color={theme.primary} />
                <span className="font-mono text-[10px]" style={{ color: theme.labelColor }}>
                  {biz.rating}
                </span>
              </div>
            )}
          </div>

          {/* Tagline — variants 0, 2, 3 */}
          {variant !== 1 && biz.tagline && (
            <p
              className="font-sans font-light text-base md:text-lg leading-relaxed max-w-md mt-4 mb-9"
              style={{ color: theme.foreSecondary, margin: heroCentered ? '1rem auto 2.25rem' : undefined }}
            >
              {biz.tagline}
            </p>
          )}
          {variant === 1 && <div className="mb-9" />}

          {/* CTAs */}
          <div className={`flex flex-wrap gap-3 ${heroCentered ? 'justify-center' : ''}`}>
            {biz.phone && (
              <a
                href={`tel:${biz.phone}`}
                className="inline-flex items-center gap-2.5 px-6 py-3.5 text-sm font-sans font-semibold tracking-wide transition-opacity hover:opacity-90"
                style={{
                  background: theme.primary,
                  color: 'white',
                  boxShadow: `0 4px 16px ${theme.primaryShadow}`,
                }}
              >
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                  <path d="M13 10.33v1.84a1.22 1.22 0 0 1-1.33 1.22 12.1 12.1 0 0 1-5.28-1.88 11.93 11.93 0 0 1-3.67-3.67A12.1 12.1 0 0 1 .84 2.47 1.22 1.22 0 0 1 2.05 1.1h1.84c.6 0 1.11.44 1.2 1.03.08.56.22 1.1.42 1.62a1.22 1.22 0 0 1-.27 1.29L4.4 5.88a9.74 9.74 0 0 0 3.67 3.67l.84-.84a1.22 1.22 0 0 1 1.29-.28c.52.2 1.06.34 1.62.42.6.09 1.04.61 1.18 1.48z" fill="currentColor"/>
                </svg>
                Call now
              </a>
            )}
            <a
              href={mapsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2.5 px-6 py-3.5 text-sm font-sans font-medium tracking-wide transition-opacity hover:opacity-70"
              style={{
                border: `1px solid ${theme.dark ? 'rgba(255,255,255,0.2)' : theme.fore + '22'}`,
                color: theme.fore,
              }}
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
                <path d="M8 1a5 5 0 0 0-5 5c0 3.5 5 9 5 9s5-5.5 5-9a5 5 0 0 0-5-5zm0 7a2 2 0 1 1 0-4 2 2 0 0 1 0 4z" fill="currentColor"/>
              </svg>
              Directions
            </a>
          </div>
        </div>
      </section>

      {/* ── About ─────────────────────────────────────────────── */}
      {hasAbout && (
        <section
          className="px-6 py-20 md:px-12 md:py-28"
          style={{ borderTop: `1px solid ${theme.border}` }}
        >
          <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-[140px_1fr] gap-10 md:gap-24 items-start">
            <p
              className="font-mono text-[10px] tracking-[0.2em] uppercase md:pt-2"
              style={{ color: theme.labelColor }}
            >
              About
            </p>
            <p
              className="font-display font-bold leading-[1.25] text-balance"
              style={{
                fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
                color: theme.dark ? theme.fore : theme.fore + 'cc',
              }}
            >
              {biz.about}
            </p>
          </div>
        </section>
      )}

      {/* ── Photo placeholder ─────────────────────────────────── */}
      {galleryPhotos.length === 0 && (
        <section
          className="px-6 py-16 md:px-12 md:py-20"
          style={{ borderTop: `1px solid ${theme.border}` }}
        >
          <div className="max-w-5xl mx-auto">
            <p
              className="font-mono text-[10px] tracking-[0.2em] uppercase mb-8"
              style={{ color: theme.labelColor }}
            >
              Photos
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5">
              {[0, 1, 2].map(i => (
                <div
                  key={i}
                  className={`flex items-center justify-center border border-dashed ${i === 0 ? 'md:col-span-2 aspect-[16/9]' : 'aspect-square'}`}
                  style={{ borderColor: theme.border, background: theme.dark ? 'rgba(255,255,255,0.02)' : theme.border + '44' }}
                >
                  <p
                    className="font-mono text-[10px] tracking-widest uppercase text-center px-4"
                    style={{ color: theme.foreSecondary, opacity: 0.5 }}
                  >
                    {i === 0 ? 'Add your photos — reply to claim this site' : 'Your photo'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Gallery ───────────────────────────────────────────── */}
      {galleryPhotos.length > 0 && (
        <section
          className="px-6 py-16 md:px-12 md:py-20"
          style={{ borderTop: `1px solid ${theme.border}` }}
        >
          <div className="max-w-5xl mx-auto">
            <p
              className="font-mono text-[10px] tracking-[0.2em] uppercase mb-8"
              style={{ color: theme.labelColor }}
            >
              Photos
            </p>
            {galleryPhotos.length === 1 ? (
              <img src={`/${galleryPhotos[0]}`} alt="" className="w-full aspect-[16/7] object-cover photo-warm" />
            ) : galleryPhotos.length === 2 ? (
              <div className="grid grid-cols-2 gap-1.5">
                {galleryPhotos.map((src, i) => (
                  <img key={i} src={`/${src}`} alt="" className="w-full aspect-square object-cover photo-warm" />
                ))}
              </div>
            ) : galleryPhotos.length === 3 ? (
              <div className="grid grid-cols-2 gap-1.5">
                <img src={`/${galleryPhotos[0]}`} alt="" className="w-full aspect-square object-cover photo-warm row-span-2" />
                <img src={`/${galleryPhotos[1]}`} alt="" className="w-full aspect-square object-cover photo-warm" />
                <img src={`/${galleryPhotos[2]}`} alt="" className="w-full aspect-square object-cover photo-warm" />
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5">
                <img src={`/${galleryPhotos[0]}`} alt="" className="w-full md:col-span-2 aspect-[16/9] object-cover photo-warm" />
                {galleryPhotos.slice(1, 7).map((src, i) => (
                  <img key={i} src={`/${src}`} alt="" className="w-full aspect-square object-cover photo-warm" />
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── PRO: Services / Menu ──────────────────────────────── */}
      {isPro && (
        <ServicesSection services={services} theme={theme} sectionLabel={servicesLabel} />
      )}

      {/* ── PRO: Reviews ──────────────────────────────────────── */}
      {isPro && (
        <ReviewsCard
          name={biz.name}
          rating={biz.rating}
          reviewCount={biz.review_count}
          address={biz.address}
          theme={theme}
        />
      )}

      {/* ── Hours + Contact ───────────────────────────────────── */}
      <section
        className="px-6 py-20 md:px-12 md:py-28"
        style={{ borderTop: `1px solid ${theme.border}` }}
      >
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-16">

          {hasHours && (
            <div>
              <p
                className="font-mono text-[10px] tracking-[0.2em] uppercase mb-8"
                style={{ color: theme.labelColor }}
              >
                Hours
              </p>
              <dl className="grid grid-cols-[60px_1fr] gap-x-6 gap-y-3.5">
                {orderedDays.map(day => {
                  const isToday = day === today
                  return (
                    <div key={day} className="contents">
                      <dt
                        className="font-mono text-[11px] uppercase tracking-widest pt-px"
                        style={{ color: isToday ? theme.primary : theme.foreSecondary, opacity: isToday ? 1 : 0.6 }}
                      >
                        {DAY_SHORT[day]}
                      </dt>
                      <dd
                        className="font-sans text-sm"
                        style={{
                          color: theme.fore,
                          fontWeight: isToday ? 500 : 300,
                          opacity: isToday ? 1 : 0.65,
                        }}
                      >
                        {hours[day]}
                      </dd>
                    </div>
                  )
                })}
              </dl>
            </div>
          )}

          <div>
            <p
              className="font-mono text-[10px] tracking-[0.2em] uppercase mb-8"
              style={{ color: theme.labelColor }}
            >
              Find us
            </p>
            <div className="flex flex-col gap-6">
              <div>
                <p
                  className="font-sans text-sm leading-relaxed font-light"
                  style={{ color: theme.foreSecondary }}
                >
                  {biz.address}
                </p>
                <a
                  href={mapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[11px] tracking-wider mt-2 inline-block transition-opacity hover:opacity-100"
                  style={{ color: theme.labelColor, opacity: 0.7 }}
                >
                  Open in Maps →
                </a>
              </div>
              {biz.phone && (
                <div>
                  <a
                    href={`tel:${biz.phone}`}
                    className="font-sans text-sm font-light transition-opacity hover:opacity-70"
                    style={{ color: theme.foreSecondary }}
                  >
                    {biz.phone}
                  </a>
                  <p
                    className="font-mono text-[10px] tracking-wide mt-0.5"
                    style={{ color: theme.foreSecondary, opacity: 0.4 }}
                  >
                    Phone
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────── */}
      <footer
        className="px-6 py-8 md:px-12"
        style={{ borderTop: `1px solid ${theme.border}` }}
      >
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
          <p
            className="font-display font-bold text-2xl"
            style={{ color: theme.fore, opacity: 0.2 }}
          >
            {biz.name}
          </p>
          <p
            className="font-mono text-[10px] tracking-widest uppercase"
            style={{ color: theme.fore, opacity: 0.15 }}
          >
            Berkeley, CA
          </p>
        </div>
      </footer>

      {/* ── PRO: AI FAQ Chat + Sticky FAB ─────────────────────── */}
      {isPro && (
        <AIFaqChat
          name={biz.name}
          phone={biz.phone}
          address={biz.address}
          hours={hours}
          services={services}
          category={biz.category}
          theme={theme}
        />
      )}

      <StickyFAB phone={biz.phone} theme={theme} />
    </main>
  )
}
