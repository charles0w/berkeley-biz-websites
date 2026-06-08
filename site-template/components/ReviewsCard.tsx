import type { Theme } from '../themes'

type Props = {
  name: string
  rating: number
  reviewCount: number
  address: string
  theme: Theme
}

function StarsFull({ rating, color }: { rating: number; color: string }) {
  const full = Math.floor(rating)
  const half = rating - full >= 0.5
  return (
    <span className="inline-flex gap-1" aria-label={`${rating} stars`}>
      {Array.from({ length: 5 }, (_, i) => (
        <svg key={i} width="16" height="16" viewBox="0 0 12 12" fill="none">
          <path
            d="M6 1l1.35 2.74L10.5 4.27l-2.25 2.19.53 3.09L6 8.02 3.22 9.55l.53-3.09L1.5 4.27l3.15-.53L6 1z"
            fill={color}
            stroke={color}
            strokeWidth="0.5"
            opacity={i < full || (half && i === full) ? 1 : 0.15}
          />
        </svg>
      ))}
    </span>
  )
}

export default function ReviewsCard({ name, rating, reviewCount, address, theme }: Props) {
  if (!rating || !reviewCount) return null

  const mapsUrl = `https://maps.google.com/?q=${encodeURIComponent(name + ' ' + address)}`
  const reviewsUrl = `https://search.google.com/local/reviews?placeid=&q=${encodeURIComponent(name + ' Berkeley')}`

  return (
    <section
      className="px-6 py-20 md:px-12 md:py-28"
      style={{ borderTop: `1px solid ${theme.border}` }}
    >
      <div className="max-w-5xl mx-auto">
        <p
          className="font-mono text-[10px] tracking-[0.2em] uppercase mb-10"
          style={{ color: theme.labelColor }}
        >
          Reviews
        </p>

        <div
          className="flex flex-col md:flex-row items-start md:items-center gap-8 p-8 md:p-10"
          style={{ background: theme.dark ? 'rgba(255,255,255,0.04)' : theme.border + '55', border: `1px solid ${theme.border}` }}
        >
          {/* Rating block */}
          <div className="flex flex-col gap-2 shrink-0">
            <span
              className="font-display font-bold leading-none"
              style={{ fontSize: '4rem', color: theme.fore }}
            >
              {rating.toFixed(1)}
            </span>
            <StarsFull rating={rating} color={theme.primary} />
            <p
              className="font-mono text-[11px] tracking-wide"
              style={{ color: theme.foreSecondary }}
            >
              {reviewCount.toLocaleString()} Google reviews
            </p>
          </div>

          {/* Divider */}
          <div
            className="hidden md:block w-px self-stretch"
            style={{ background: theme.border }}
          />

          {/* CTA */}
          <div className="flex flex-col gap-3">
            <p
              className="font-sans text-sm font-light leading-relaxed max-w-xs"
              style={{ color: theme.foreSecondary }}
            >
              Customers keep coming back. Read what they say about {name} on Google.
            </p>
            <a
              href={mapsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 font-mono text-[11px] tracking-wider uppercase transition-opacity hover:opacity-70"
              style={{ color: theme.primary }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
              Read all reviews on Google
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
