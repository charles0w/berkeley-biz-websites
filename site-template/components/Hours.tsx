import { business } from "@/lib/business";

// Hours — editorial table treatment with mono price/time marks.
//
// Differs from the previous template:
//  - Background changed from stone-100 to bg-paper (warm paper tone, not cool grey).
//  - Hours rendered in mono with hairline dividers — magazine, not invoice.
//  - Asymmetric 4/8 split: heading + address in left rail, day list in right column.
//  - "Open in Google Maps" upgraded from underline link to real CTA button.

export default function Hours() {
  const { hours_raw, address, google_maps_url } = business;

  return (
    <section id="hours" className="relative z-10 bg-paper">
      <div className="max-w-7xl mx-auto px-6 md:px-10 py-20 md:py-28">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 md:gap-12">
          <div className="md:col-span-4">
            <p className="text-mute text-[11px] tracking-extra-wide uppercase font-mono mb-3 reveal">
              Hours
            </p>
            <h2 className="font-display text-espresso text-[40px] md:text-[52px] leading-[1.05] tracking-tightest reveal">
              When we&apos;re<br />
              <span className="display-italic">open.</span>
            </h2>

            <div className="mt-8 space-y-4 reveal">
              <div>
                <p className="text-mute text-[11px] tracking-extra-wide uppercase font-mono mb-2">
                  Address
                </p>
                <address className="not-italic text-espresso text-[16px] leading-relaxed">
                  {address}
                </address>
              </div>

              {google_maps_url && (
                <a
                  href={google_maps_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="press inline-flex items-center gap-2 mt-2 px-5 py-3 border border-espresso/15 text-espresso rounded-sharp text-[14px] tracking-wide hover:border-espresso/40 transition-colors"
                >
                  <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                    <path
                      d="M7 13C7 13 12 8.4 12 5.5A5 5 0 0 0 2 5.5C2 8.4 7 13 7 13Z"
                      stroke="currentColor"
                      strokeWidth="1"
                      strokeLinejoin="round"
                    />
                    <circle cx="7" cy="5.5" r="1.6" stroke="currentColor" strokeWidth="1" />
                  </svg>
                  Open in Google Maps
                </a>
              )}
            </div>
          </div>

          <div className="md:col-span-8 md:pl-8 lg:pl-16 md:border-l md:border-espresso/10">
            <ul className="divide-y divide-espresso/8">
              {hours_raw.map((line, i) => {
                const [day, ...rest] = line.split(":");
                const time = rest.join(":").trim();
                return (
                  <li key={i} className="flex items-center justify-between py-4 reveal">
                    <span className="text-espresso text-[15px] tracking-wide">{day}</span>
                    <span className="font-mono text-[14px] text-espresso-soft">
                      {time || "Closed"}
                    </span>
                  </li>
                );
              })}
            </ul>

            <p className="text-mute text-[12px] tracking-extra-wide uppercase font-mono mt-6 reveal">
              Hours pulled from Google. Confirm with the shop before a long drive.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
