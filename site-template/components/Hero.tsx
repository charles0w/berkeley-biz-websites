import { business } from "@/lib/business";

// Hero — Editorial Luxury archetype, with a no-photo fallback.
//
// Differs from the previous template:
//  - No `h-screen` (banned by design-taste-frontend; use `min-h-[100dvh]` on mobile).
//  - No dark gradient overlay over a hero image.
//  - Asymmetric two-column layout: large display headline left, layered photo right.
//  - Tap-to-call is the primary CTA in espresso.
//  - **No-photo fallback:** when business.photos.hero is missing or a placeholder,
//    render a single-column typographic hero. ~22% of generated sites had no real
//    photos from Google Maps; rendering a broken <img> looked terrible. The
//    typographic-only treatment is intentional and reads as editorial, not broken.

function isRealPhoto(p: string | undefined): boolean {
  if (!p) return false;
  if (p.includes("placeholder")) return false;
  return true;
}

export default function Hero() {
  const phoneDigits = business.phone.replace(/\D/g, "");
  const heroPhoto = business.photos.hero;
  const galleryFallback = business.photos.gallery[0];
  const showRating = business.rating > 0;

  const hasHero = isRealPhoto(heroPhoto);
  const hasSecond = isRealPhoto(galleryFallback) && galleryFallback !== heroPhoto;

  // No-photo path: full-width typographic hero.
  if (!hasHero) {
    return (
      <section className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 pt-10 md:pt-16 pb-16 md:pb-24 min-h-[80dvh]">
        <div className="max-w-4xl">
          <p className="text-mute text-[12px] tracking-extra-wide uppercase mb-6 reveal">
            <span className="inline-block w-8 h-px bg-mute align-middle mr-3" />
            {business.category} · Berkeley
          </p>

          <h1 className="font-display text-espresso text-[56px] sm:text-[80px] md:text-[112px] lg:text-[136px] leading-[0.94] tracking-tightest reveal">
            {business.name}
          </h1>

          {business.tagline && (
            <p className="mt-10 font-display display-italic text-espresso-soft text-[24px] md:text-[32px] leading-[1.3] max-w-[40ch] reveal">
              {business.tagline}
            </p>
          )}

          <div className="mt-12 flex flex-wrap items-center gap-3 reveal">
            {business.phone && (
              <a
                href={`tel:${phoneDigits}`}
                className="press inline-flex items-center gap-2 px-6 py-3.5 bg-espresso text-cream rounded-sharp text-[15px] tracking-wide hover:bg-espresso-ink transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                  <path
                    d="M3 1.5C3 1.5 3.5 1 4 1H5L6 4L4.5 5C5 6.5 6.5 8 8 8.5L9 7L12 8V9C12 9.5 11.5 10 11.5 10C8 10 3 5 3 1.5Z"
                    stroke="currentColor"
                    strokeWidth="1.1"
                    strokeLinejoin="round"
                  />
                </svg>
                {business.phone}
              </a>
            )}
            {business.google_maps_url && (
              <a
                href={business.google_maps_url}
                target="_blank"
                rel="noopener noreferrer"
                className="press inline-flex items-center gap-2 px-6 py-3.5 border border-espresso/15 text-espresso rounded-sharp text-[15px] tracking-wide hover:border-espresso/40 transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path
                    d="M7 13C7 13 12 8.4 12 5.5A5 5 0 0 0 2 5.5C2 8.4 7 13 7 13Z"
                    stroke="currentColor"
                    strokeWidth="1"
                    strokeLinejoin="round"
                  />
                  <circle cx="7" cy="5.5" r="1.6" stroke="currentColor" strokeWidth="1" />
                </svg>
                Get directions
              </a>
            )}
          </div>

          <div className="mt-12 flex flex-wrap items-center gap-x-6 gap-y-2 text-[13px] text-espresso-soft reveal">
            <div className="inline-flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sage pulse-dot" />
              <span className="tracking-wide">Open now</span>
            </div>
            {showRating && (
              <>
                <span className="text-mute">·</span>
                <span className="tracking-wide">{business.rating.toFixed(1)} on Google</span>
              </>
            )}
          </div>
        </div>
      </section>
    );
  }

  // Photo path: asymmetric two-column with layered photo treatment.
  return (
    <section className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 pt-10 md:pt-16 pb-16 md:pb-24 min-h-[80dvh]">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-end">
        <div className="lg:col-span-7">
          <p className="text-mute text-[12px] tracking-extra-wide uppercase mb-6 reveal">
            <span className="inline-block w-8 h-px bg-mute align-middle mr-3" />
            {business.category} · Berkeley
          </p>

          <h1 className="font-display text-espresso text-[52px] sm:text-[68px] md:text-[88px] lg:text-[104px] leading-[0.96] tracking-tightest reveal">
            {business.name}
          </h1>

          {business.tagline && (
            <p className="mt-8 font-display display-italic text-espresso-soft text-[22px] md:text-[28px] leading-[1.3] max-w-[36ch] reveal">
              {business.tagline}
            </p>
          )}

          <div className="mt-10 flex flex-wrap items-center gap-3 reveal">
            {business.phone && (
              <a
                href={`tel:${phoneDigits}`}
                className="press inline-flex items-center gap-2 px-6 py-3.5 bg-espresso text-cream rounded-sharp text-[15px] tracking-wide hover:bg-espresso-ink transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                  <path
                    d="M3 1.5C3 1.5 3.5 1 4 1H5L6 4L4.5 5C5 6.5 6.5 8 8 8.5L9 7L12 8V9C12 9.5 11.5 10 11.5 10C8 10 3 5 3 1.5Z"
                    stroke="currentColor"
                    strokeWidth="1.1"
                    strokeLinejoin="round"
                  />
                </svg>
                {business.phone}
              </a>
            )}
            {business.google_maps_url && (
              <a
                href={business.google_maps_url}
                target="_blank"
                rel="noopener noreferrer"
                className="press inline-flex items-center gap-2 px-6 py-3.5 border border-espresso/15 text-espresso rounded-sharp text-[15px] tracking-wide hover:border-espresso/40 transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path
                    d="M7 13C7 13 12 8.4 12 5.5A5 5 0 0 0 2 5.5C2 8.4 7 13 7 13Z"
                    stroke="currentColor"
                    strokeWidth="1"
                    strokeLinejoin="round"
                  />
                  <circle cx="7" cy="5.5" r="1.6" stroke="currentColor" strokeWidth="1" />
                </svg>
                Get directions
              </a>
            )}
          </div>

          <div className="mt-12 flex flex-wrap items-center gap-x-6 gap-y-2 text-[13px] text-espresso-soft reveal">
            <div className="inline-flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sage pulse-dot" />
              <span className="tracking-wide">Open now</span>
            </div>
            {showRating && (
              <>
                <span className="text-mute">·</span>
                <span className="tracking-wide">{business.rating.toFixed(1)} on Google</span>
              </>
            )}
          </div>
        </div>

        <div className="lg:col-span-5 relative reveal">
          <div className="relative aspect-[4/5] bg-paper overflow-hidden shadow-ambient-lg">
            <img
              src={heroPhoto}
              alt={`${business.name} interior`}
              className="absolute inset-0 w-full h-full object-cover photo-warm"
              loading="eager"
              decoding="async"
            />
            <div className="absolute bottom-4 left-4 right-4 text-cream text-[11px] tracking-extra-wide uppercase font-mono opacity-85">
              <span>{business.address.split(",")[0]}</span>
              <span className="mx-2">·</span>
              <span>open today</span>
            </div>
          </div>

          {hasSecond && (
            <div className="hidden md:block absolute -bottom-8 -left-10 w-40 h-52 bg-paper overflow-hidden shadow-ambient -z-10">
              <img
                src={galleryFallback}
                alt={`${business.name} detail`}
                className="w-full h-full object-cover photo-warm"
                loading="lazy"
                decoding="async"
              />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
