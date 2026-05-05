import { business } from "@/lib/business";

// About — editorial two-column layout.
//
// Differs from the previous template:
//  - Asymmetric 5/7 column split (eyebrow + heading on the left, prose on the
//    right) instead of a centred narrow column.
//  - Heading uses the actual business category instead of a generic "institution".
//  - Rating block redesigned: large numeric value next to a typographic
//    "Google rating / out of 5" descriptor, not the gold-star row that read
//    like a Google embed.

export default function About() {
  const showRating = business.rating > 0;

  return (
    <section id="about" className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 py-20 md:py-28">
      <div className="hairline pt-12 md:pt-16">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 md:gap-12">
          <div className="md:col-span-5">
            <p className="text-mute text-[11px] tracking-extra-wide uppercase font-mono mb-3 reveal">
              About
            </p>
            <h2 className="font-display text-espresso text-[40px] md:text-[56px] leading-[1.02] tracking-tightest reveal">
              A neighborhood<br />
              <span className="display-italic">{business.category.toLowerCase()}.</span>
            </h2>
          </div>

          <div className="md:col-span-7 md:pl-8 lg:pl-16 md:border-l md:border-espresso/10">
            <p className="text-espresso-soft text-[17px] md:text-[18px] leading-[1.65] max-w-[60ch] reveal">
              {business.about}
            </p>

            {showRating && (
              <div className="mt-12 flex items-baseline gap-6 reveal">
                <span className="font-display text-espresso text-[64px] leading-none tracking-tightest">
                  {business.rating.toFixed(1)}
                </span>
                <div className="text-espresso-soft text-[14px] leading-tight">
                  <p className="font-mono text-[12px] tracking-extra-wide uppercase text-mute mb-1">
                    Google rating
                  </p>
                  <p>out of 5</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
