"use client";

import { useEffect, useState } from "react";
import { business } from "@/lib/business";

/**
 * StickyCallCTA — mobile-only sticky tap-to-call FAB.
 *
 * Per the sellable-website-checklist 10-second test:
 *  - Tap-to-call is the #1 conversion action for restaurants/salons.
 *  - It must be reachable at every scroll position on mobile.
 *
 * Behaviour:
 *  - Hidden until the user has scrolled past 380px (so it doesn't overlap the
 *    hero CTAs which already include a tap-to-call button).
 *  - Mobile-only — desktop nav has a persistent call button instead.
 *  - Bottom-fixed with the same espresso treatment as the primary CTAs in Hero
 *    and Contact, so the visual vocabulary stays consistent.
 *  - The FAB itself has reveal animation; the actual tel: link is always live.
 */
export default function StickyCallCTA() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 380);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (!business.phone) return null;
  const phoneDigits = business.phone.replace(/\D/g, "");

  return (
    <a
      href={`tel:${phoneDigits}`}
      className={`sticky-call md:hidden fixed bottom-5 left-5 right-5 z-50 press ${
        visible ? "is-visible" : "is-hidden"
      }`}
      aria-label={`Call ${business.name} at ${business.phone}`}
    >
      <span className="flex items-center justify-center gap-2 px-6 py-4 bg-espresso text-cream rounded-sharp shadow-ambient-lg text-[15px] tracking-wide">
        <svg width="14" height="14" viewBox="0 0 13 13" fill="none" aria-hidden="true">
          <path
            d="M3 1.5C3 1.5 3.5 1 4 1H5L6 4L4.5 5C5 6.5 6.5 8 8 8.5L9 7L12 8V9C12 9.5 11.5 10 11.5 10C8 10 3 5 3 1.5Z"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />
        </svg>
        Call {business.phone}
      </span>
    </a>
  );
}
