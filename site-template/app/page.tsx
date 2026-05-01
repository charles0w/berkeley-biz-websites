import business from '../business.json'
import StickyFAB from '../components/StickyFAB'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const DAY_SHORT: Record<string, string> = {
  Monday: 'Mon', Tuesday: 'Tue', Wednesday: 'Wed', Thursday: 'Thu',
  Friday: 'Fri', Saturday: 'Sat', Sunday: 'Sun',
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.floor(rating)
  const half = rating - full >= 0.5
  return (
    <span className="inline-flex gap-0.5" aria-label={`${rating} stars`}>
      {Array.from({ length: 5 }, (_, i) => (
        <svg key={i} width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden>
          <path
            d="M6 1l1.35 2.74L10.5 4.27l-2.25 2.19.53 3.09L6 8.02 3.22 9.55l.53-3.09L1.5 4.27l3.15-.53L6 1z"
            fill={i < full ? '#78716c' : half && i === full ? '#78716c' : 'none'}
            stroke="#78716c"
            strokeWidth="0.75"
          />
        </svg>
      ))}
    </span>
  )
}

export default function Page() {
  const photos = business.photos
  const heroPhoto = photos[0]
  const accentPhoto = photos[1]
  const galleryPhotos = photos.slice(2, 5)

  const hours = business.hours as Record<string, string>
  const orderedDays = DAYS.filter(d => d in hours)

  const cityLine = business.address.split(',').slice(1).join(',').trim()

  return (
    <main className="min-h-[100dvh] bg-stone-50">

      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section className="px-6 pt-12 pb-0 md:px-16 md:pt-20 lg:px-24">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-16 items-start">

          {/* Left — identity */}
          <div className="flex flex-col">
            <p className="font-mono text-[10px] tracking-[0.18em] uppercase text-stone-400 mb-7">
              {cityLine}
            </p>

            <h1 className="font-display font-light italic text-stone-900 leading-display tracking-tightest text-balance mb-5"
              style={{ fontSize: 'clamp(2.4rem, 5.5vw, 4.4rem)' }}>
              {business.name}
            </h1>

            <p className="font-sans font-light text-stone-500 text-lg leading-snug mb-8 max-w-xs">
              {business.tagline}
            </p>

            <div className="flex items-center gap-2.5 mb-10">
              <StarRating rating={business.rating} />
              <span className="font-mono text-xs text-stone-400">
                {business.rating} &middot; {business.review_count.toLocaleString()} reviews
              </span>
            </div>

            <a
              href={`tel:${business.phone}`}
              className="self-start inline-flex items-center gap-2.5 bg-stone-900 text-stone-50 px-6 py-3 text-sm font-sans font-medium tracking-wide hover:bg-stone-800 active:bg-stone-700 transition-colors shadow-ambient"
            >
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden>
                <path d="M13 10.33v1.84a1.22 1.22 0 0 1-1.33 1.22 12.1 12.1 0 0 1-5.28-1.88 11.93 11.93 0 0 1-3.67-3.67A12.1 12.1 0 0 1 .84 2.47 1.22 1.22 0 0 1 2.05 1.1h1.84c.6 0 1.11.44 1.2 1.03.08.56.22 1.1.42 1.62a1.22 1.22 0 0 1-.27 1.29L4.4 5.88a9.74 9.74 0 0 0 3.67 3.67l.84-.84a1.22 1.22 0 0 1 1.29-.28c.52.2 1.06.34 1.62.42.6.09 1.04.61 1.18 1.48z" fill="currentColor"/>
              </svg>
              {business.phone}
            </a>
          </div>

          {/* Right — layered photos */}
          <div className="relative mt-4 md:mt-0">
            {heroPhoto && (
              <img
                src={`/${heroPhoto}`}
                alt={business.name}
                className="w-full aspect-[4/5] object-cover photo-warm shadow-ambient-lg"
              />
            )}
            {accentPhoto && (
              <img
                src={`/${accentPhoto}`}
                alt=""
                className="absolute -bottom-8 -left-8 w-[46%] aspect-square object-cover photo-warm shadow-ambient-md border-[3px] border-stone-50 hidden md:block"
              />
            )}
          </div>
        </div>
      </section>

      {/* ── About ─────────────────────────────────────────────────── */}
      <section className="px-6 pt-24 pb-0 md:px-16 lg:px-24">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-[200px_1fr] gap-8 md:gap-16 items-start">
          <p className="font-mono text-[10px] tracking-[0.18em] uppercase text-stone-400 md:pt-1.5">
            About
          </p>
          <p className="font-sans font-light text-stone-600 text-[1.05rem] leading-[1.75] max-w-prose">
            {business.about}
          </p>
        </div>
      </section>

      {/* ── Hours ─────────────────────────────────────────────────── */}
      {orderedDays.length > 0 && (
        <section className="px-6 pt-16 pb-0 md:px-16 lg:px-24">
          <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-[200px_1fr] gap-8 md:gap-16 items-start">
            <p className="font-mono text-[10px] tracking-[0.18em] uppercase text-stone-400 md:pt-1">
              Hours
            </p>
            <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-2.5 max-w-xs">
              {orderedDays.map(day => (
                <>
                  <dt key={`d-${day}`} className="font-mono text-[11px] uppercase tracking-widest text-stone-400 pt-px">
                    {DAY_SHORT[day]}
                  </dt>
                  <dd key={`t-${day}`} className="font-sans text-sm text-stone-700 font-light">
                    {hours[day]}
                  </dd>
                </>
              ))}
            </dl>
          </div>
        </section>
      )}

      {/* ── Gallery ───────────────────────────────────────────────── */}
      {galleryPhotos.length > 0 && (
        <section className="px-6 pt-16 pb-0 md:px-16 lg:px-24">
          <div className="max-w-6xl mx-auto">
            <div className={`grid gap-2 ${galleryPhotos.length === 1 ? 'grid-cols-1' : galleryPhotos.length === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
              {galleryPhotos.map((src, i) => (
                <img
                  key={i}
                  src={`/${src}`}
                  alt=""
                  className="w-full aspect-square object-cover photo-warm"
                />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer className="px-6 pt-16 pb-12 md:px-16 lg:px-24">
        <div className="max-w-6xl mx-auto border-t border-stone-200 pt-8 flex flex-col md:flex-row justify-between gap-4">
          <div>
            <p className="font-mono text-[11px] text-stone-400 tracking-wide">{business.address}</p>
          </div>
          <div className="flex flex-col gap-1">
            <a
              href={`tel:${business.phone}`}
              className="font-mono text-[11px] text-stone-400 tracking-wide hover:text-stone-700 transition-colors"
            >
              {business.phone}
            </a>
            <a
              href={`https://maps.google.com/?q=${encodeURIComponent(business.address)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-[11px] text-stone-400 tracking-wide hover:text-stone-700 transition-colors"
            >
              Get directions
            </a>
          </div>
        </div>
      </footer>

      <StickyFAB phone={business.phone} />
    </main>
  )
}
