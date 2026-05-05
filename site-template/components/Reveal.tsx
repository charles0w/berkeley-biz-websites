"use client";

import { useEffect } from "react";

/**
 * Reveal — global reveal-on-scroll observer.
 *
 * The CSS class `.reveal` (defined in app/globals.css) has the initial state
 * (opacity-0, translateY) and the final state when `.in` is added. This
 * component sets up an IntersectionObserver once at mount and adds `.in` to
 * each `.reveal` element as it enters the viewport.
 *
 * Mounted by app/page.tsx so all sections benefit from it without each
 * needing to be a client component.
 */
export default function Reveal() {
  useEffect(() => {
    if (typeof window === "undefined") return;

    const els = document.querySelectorAll(".reveal");
    if (els.length === 0) return;

    // Respect reduced-motion preference — instantly reveal everything.
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    if (prefersReducedMotion) {
      els.forEach((el) => el.classList.add("in"));
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { rootMargin: "0px 0px -60px 0px", threshold: 0.05 }
    );

    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return null;
}
