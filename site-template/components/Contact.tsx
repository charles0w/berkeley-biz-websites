import { business } from "@/lib/business";

// Contact — visit + tap-to-call section.
//
// Differs from the previous template:
//  - No more centred narrow column. Asymmetric 5/7 split puts the heading +
//    structured contact metadata on the left, an embedded map on the right.
//  - Tap-to-call is the primary CTA in espresso (matching Hero); Get
//    Directions is the secondary outline button.
//  - The static map iframe gives a real spatial sense of where the business is.
//  - Section id retained as "contact" so existing in-page anchors still resolve.

export default function Contact() {
  const phoneDigits = business.phone.replace(/\D/g, "");
  const mapsQuery = encodeURIComponent(business.address);
  const mapEmbedSrc = `https://www.google.com/maps?q=${mapsQuery}&output=embed`;

  return (
    <section id="contact" className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 py-20 md:py-28">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14">
        <div className="lg:col-span-5">
          <p className="text-mute text-[11px] tracking-extra-wide uppercase font-mono mb-3 reveal">
            Visit
          </p>
          <h2 className="font-display text-espresso text-[40px] md:text-[56px] leading-[1.02] tracking-tightest reveal">
            Stop by,<br />
            <span className="display-italic">say hello.</span>
          </h2>

          <div className="mt-10 space-y-7 reveal">
            <div>
              <p className="text-mute text-[11px] tracking-extra-wide uppercase font-mono mb-2">
                Address
              </p>
              <p className="text-espresso text-[16px] leading-relaxed">
                {business.address}
              </p>
            </div>
            {business.phone && (
              <div>
                <p className="text-mute text-[11px] tracking-extra-wide uppercase font-mono mb-2">
                  Phone
                </p>
                <a
                  href={`tel:${phoneDigits}`}
                  className="font-mono text-espresso text-[16px] hover:text-[var(--accent)] transition-colors"
                >
                  {business.phone}
                </a>
              </div>
            )}
          </div>

          <div className="mt-10 flex flex-wrap gap-3 reveal">
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
                Call
              </a>
            )}
            {(business.google_maps_url || business.address) && (
              <a
                href={
                  business.google_maps_url ||
                  `https://maps.google.com/?q=${mapsQuery}`
                }
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
                Directions
              </a>
            )}
          </div>
        </div>

        <div className="lg:col-span-7 reveal">
          <div className="aspect-[4/3] lg:aspect-square overflow-hidden bg-paper shadow-ambient">
            <iframe
              src={mapEmbedSrc}
              width="100%"
              height="100%"
              style={{ border: 0, filter: "grayscale(0.25) saturate(0.85)" }}
              allowFullScreen
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              title={`Map of ${business.name}, ${business.address}`}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
