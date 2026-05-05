import { business } from "@/lib/business";

// Footer — minimal, monoline.
//
// Differs from the previous template:
//  - Hairline divider replaces the border-top + bg-stone-50 block.
//  - Mark + name aligned baseline-style with the same SVG used in Nav.
//  - Mono-line address + phone in JetBrains Mono — same typographic vocabulary.
//  - Discreet "sample site" disclaimer added.

export default function Footer() {
  return (
    <footer className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 py-12 md:py-16 hairline mt-12">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="flex items-baseline gap-3">
          <svg
            width="18"
            height="18"
            viewBox="0 0 22 22"
            className="text-espresso translate-y-[1px]"
            fill="none"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="9.5" stroke="currentColor" strokeWidth="1" />
            <path
              d="M3.5 11 A 7.5 7.5 0 0 0 18.5 11"
              stroke="currentColor"
              strokeWidth="1"
              strokeLinecap="round"
            />
          </svg>
          <span className="font-display text-espresso text-[16px] tracking-tightest">
            {business.name}
          </span>
        </div>

        <div className="text-mute text-[12px] tracking-wide font-mono">
          {business.address}
          {business.phone && (
            <>
              <span className="mx-2">·</span>
              {business.phone}
            </>
          )}
        </div>
      </div>

      <p className="mt-6 text-mute text-[11px] tracking-extra-wide uppercase font-mono">
        Sample site built for review · &copy; {new Date().getFullYear()} {business.name}
      </p>
    </footer>
  );
}
