import business from '../business.json'
import StickyFAB from '../components/StickyFAB'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const DAY_SHORT: Record<string, string> = {
  Monday: 'Mon', Tuesday: 'Tue', Wednesday: 'Wed', Thursday: 'Thu',
  Friday: 'Fri', Saturday: 'Sat', Sunday: 'Sun',
}

function Stars({ rating }: { rating: number }) {
  const full = Math.floor(rating)
  const half = rating - full >= 0.5
  return (
    <span className="inline-flex gap-0.5" aria-label={`${rating} stars`}>
      {Array.from({ length: 5 }, (_, i) => (
        <svg key={i} width="14" height="14" viewBox="0 0 12 12" fill="none">
          <path
            d="M6 1l1.35 2.74L10.5 4.27l-2.25 2.19.53 3.09L6 8.02 3.22 9.55l.53-3.09L1.5 4.27l3.15-.53L6 1z"
            fill="currentColor"
            stroke="currentColor"
            strokeWidth="0.75"
            opacity={i < full || (half && i === full) ? 1 : 0.2}
          />
        </svg>
      ))}
    </span>
  )
}

export default function Page() {
  const photos = (business.photos ?? []) as string[]
  const heroPhoto = photos[0]
  // Gallery shows all photos — gives the most visual richness
  const galleryPhotos = photos.slice(0, 8)
  const hours = (business.hours ?? {}) as Record<string, string>
  const orderedDays = DAYS.filter(d => d in hours)
  const hasHours = orderedDays.length > 0
  const hasAbout = Boolean((business as any).about?.trim())
  const about = (business as any).about ?? ''

  const streetLine = business.address.split(',')[0]?.trim() ?? ''
  const cityLine = business.address.split(',').slice(1).join(',').trim()
  const mapsUrl = `https://maps.google.com/?q=${encodeURIComponent(business.address)}`

  // Category-specific gradient for businesses with no photo
  const categoryGradient: Record<string, string> = {
    cafe:     'from-amber-950 via-stone-900 to-neutral-950',
    food:     'from-orange-950 via-stone-900 to-neutral-950',
    salon:    'from-rose-950 via-stone-900 to-neutral-950',
    beauty:   'from-pink-950 via-stone-900 to-neutral-950',
    fitness:  'from-blue-950 via-slate-900 to-neutral-950',
    retail:   'from-violet-950 via-stone-900 to-neutral-950',
    services: 'from-teal-950 via-stone-900 to-neutral-950',
  }
  const heroGradient = categoryGradient[business.category as string] ?? 'from-stone-900 to-neutral-950'

  return (
    <main className="min-h-[100dvh] bg-neutral-950 text-neutral-100">

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative h-[100svh] min-h-[600px] flex flex-col">
        {heroPhoto ? (
          <img
            src={`/${heroPhoto}`}
            alt={business.name}
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <div className={`absolute inset-0 bg-gradient-to-br ${heroGradient}`} />
        )}

        {/* Gradient: strong at bottom for text, subtle at top */}
        <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/55 to-neutral-950/15" />

        {/* Top bar */}
        <div className="relative z-10 flex items-center justify-between px-6 pt-7 md:px-12">
          <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/50">
            {cityLine || 'Berkeley, CA'}
          </span>
          {business.phone && (
            <a
              href={`tel:${business.phone}`}
              className="font-mono text-[11px] tracking-wider text-white/50 hover:text-white transition-colors"
            >
              {business.phone}
            </a>
          )}
        </div>

        {/* Hero content — pinned to bottom-left */}
        <div className="relative z-10 mt-auto px-6 pb-12 md:px-12 md:pb-16 max-w-4xl">
          {business.rating > 0 && (
            <div className="inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/10">
              <Stars rating={business.rating} />
              <span className="font-mono text-[11px] text-white/60">
                {business.rating} · {business.review_count.toLocaleString()} Google reviews
              </span>
            </div>
          )}

          <h1
            className="font-display font-light italic text-white leading-[1.02] tracking-tight text-balance mb-5"
            style={{ fontSize: 'clamp(3rem, 7.5vw, 5.5rem)' }}
          >
            {business.name}
          </h1>

          <p className="font-sans font-light text-white/60 text-base md:text-lg leading-relaxed max-w-lg mb-9">
            {business.tagline || `${streetLine} · ${cityLine}`}
          </p>

          <div className="flex flex-wrap gap-3">
            {business.phone && (
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center gap-2.5 bg-white text-neutral-900 px-6 py-3.5 text-sm font-sans font-semibold tracking-wide hover:bg-neutral-100 transition-colors shadow-lg"
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
              className="inline-flex items-center gap-2.5 bg-white/10 text-white border border-white/20 px-6 py-3.5 text-sm font-sans font-medium tracking-wide hover:bg-white/20 transition-colors backdrop-blur-sm"
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
        <section className="px-6 py-20 md:px-12 md:py-28 border-t border-white/5">
          <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-[160px_1fr] gap-10 md:gap-24 items-start">
            <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/25 md:pt-2">
              About
            </p>
            <p className="font-display italic font-light text-white/85 leading-[1.7] text-xl md:text-2xl max-w-2xl">
              {about}
            </p>
          </div>
        </section>
      )}

      {/* ── Photo placeholder for businesses with no photos ───── */}
      {galleryPhotos.length === 0 && (
        <section className="px-6 py-16 md:px-12 md:py-20 border-t border-white/5">
          <div className="max-w-5xl mx-auto">
            <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/25 mb-8">Photos</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5">
              {[0,1,2].map(i => (
                <div key={i} className={`flex items-center justify-center border border-dashed border-white/8 ${i === 0 ? 'md:col-span-2 aspect-[16/9]' : 'aspect-square'} bg-white/[0.02]`}>
                  <p className="font-mono text-[10px] tracking-widest uppercase text-white/15 text-center px-4">
                    {i === 0 ? 'Add your own photos — reply to claim this site' : 'Your photo'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Gallery ───────────────────────────────────────────── */}
      {galleryPhotos.length > 0 && (
        <section className="px-6 py-16 md:px-12 md:py-20 border-t border-white/5">
          <div className="max-w-5xl mx-auto">
            <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/25 mb-8">Photos</p>
            {galleryPhotos.length === 1 ? (
              <img src={`/${galleryPhotos[0]}`} alt="" className="w-full aspect-[16/7] object-cover" />
            ) : galleryPhotos.length === 2 ? (
              <div className="grid grid-cols-2 gap-1.5">
                {galleryPhotos.map((src, i) => (
                  <img key={i} src={`/${src}`} alt="" className="w-full aspect-square object-cover" />
                ))}
              </div>
            ) : galleryPhotos.length === 3 ? (
              <div className="grid grid-cols-2 gap-1.5">
                <img src={`/${galleryPhotos[0]}`} alt="" className="w-full aspect-square object-cover row-span-2" />
                <img src={`/${galleryPhotos[1]}`} alt="" className="w-full aspect-square object-cover" />
                <img src={`/${galleryPhotos[2]}`} alt="" className="w-full aspect-square object-cover" />
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5">
                <img src={`/${galleryPhotos[0]}`} alt="" className="w-full md:col-span-2 aspect-[16/9] object-cover" />
                {galleryPhotos.slice(1, 7).map((src, i) => (
                  <img key={i} src={`/${src}`} alt="" className="w-full aspect-square object-cover" />
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── Hours + Contact ───────────────────────────────────── */}
      <section className="px-6 py-20 md:px-12 md:py-28 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-16">

          {hasHours && (
            <div>
              <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/25 mb-8">Hours</p>
              <dl className="grid grid-cols-[60px_1fr] gap-x-6 gap-y-3">
                {orderedDays.map(day => (
                  <>
                    <dt key={`d-${day}`} className="font-mono text-[11px] uppercase tracking-widest text-white/25 pt-px">
                      {DAY_SHORT[day]}
                    </dt>
                    <dd key={`t-${day}`} className="font-sans text-sm text-white/65 font-light">
                      {hours[day]}
                    </dd>
                  </>
                ))}
              </dl>
            </div>
          )}

          <div>
            <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/25 mb-8">Find us</p>
            <div className="flex flex-col gap-6">
              <div>
                <p className="font-sans text-white/75 text-sm leading-relaxed font-light">
                  {business.address}
                </p>
                <a
                  href={mapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[11px] tracking-wider text-white/25 hover:text-white/55 transition-colors mt-2 inline-block"
                >
                  Open in Maps →
                </a>
              </div>
              {business.phone && (
                <div>
                  <a
                    href={`tel:${business.phone}`}
                    className="font-sans text-white/75 text-sm font-light hover:text-white transition-colors"
                  >
                    {business.phone}
                  </a>
                  <p className="font-mono text-[10px] text-white/20 tracking-wide mt-0.5">Phone</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────── */}
      <footer className="px-6 py-8 md:px-12 border-t border-white/5">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
          <p className="font-display italic text-white/15 text-sm">{business.name}</p>
          <p className="font-mono text-[10px] tracking-widest uppercase text-white/10">Berkeley, CA</p>
        </div>
      </footer>

      <StickyFAB phone={business.phone} />
    </main>
  )
}
