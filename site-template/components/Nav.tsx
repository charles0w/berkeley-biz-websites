"use client";

import { business } from "@/lib/business";

// Nav — minimal hairline-divider header.
//
// Differs from the previous template:
//  - No fixed translucent overlay over the hero.
//  - Tap-to-call always visible (desktop full button, mobile compact pill).
//  - Removed the dual scrolled/unscrolled style switch.

export default function Nav() {
  const phoneDigits = business.phone.replace(/\D/g, "");
  const galleryShown = business.photos.gallery.length > 0;

  return (
    <header className="relative z-30 max-w-7xl mx-auto px-6 md:px-10 pt-6 md:pt-8">
      <div className="flex items-center justify-between">
        <a href="#" className="flex items-baseline gap-3 group">
          <svg
            width="22"
            height="22"
            viewBox="0 0 22 22"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="text-espresso translate-y-[1px]"
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
          <span className="font-display text-[19px] tracking-tightest text-espresso">
            {business.name}
          </span>
        </a>

        <nav className="hidden md:flex items-center gap-9 text-[14px] text-espresso-soft">
          <a href="#about" className="nav-link">About</a>
          {galleryShown && <a href="#gallery" className="nav-link">Gallery</a>}
          <a href="#hours" className="nav-link">Visit</a>
          {business.phone && (
            <a
              href={`tel:${phoneDigits}`}
              className="press inline-flex items-center gap-2 px-4 py-2 bg-espresso text-cream rounded-sharp hover:bg-espresso-ink transition-colors"
            >
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path
                  d="M3 1.5C3 1.5 3.5 1 4 1H5L6 4L4.5 5C5 6.5 6.5 8 8 8.5L9 7L12 8V9C12 9.5 11.5 10 11.5 10C8 10 3 5 3 1.5Z"
                  stroke="currentColor"
                  strokeWidth="1.1"
                  strokeLinejoin="round"
                />
              </svg>
              <span className="tracking-wide">{business.phone}</span>
            </a>
          )}
        </nav>

        {business.phone && (
          <a
            href={`tel:${phoneDigits}`}
            className="md:hidden press inline-flex items-center gap-2 px-3 py-2 bg-espresso text-cream rounded-sharp text-[13px]"
          >
            <svg width="12" height="12" viewBox="0 0 13 13" fill="none" aria-hidden="true">
              <path
                d="M3 1.5C3 1.5 3.5 1 4 1H5L6 4L4.5 5C5 6.5 6.5 8 8 8.5L9 7L12 8V9C12 9.5 11.5 10 11.5 10C8 10 3 5 3 1.5Z"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeLinejoin="round"
              />
            </svg>
            <span>Call</span>
          </a>
        )}
      </div>
    </header>
  );
}
