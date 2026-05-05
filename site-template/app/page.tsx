import { business } from "@/lib/business";
import Nav from "@/components/Nav";
import Hero from "@/components/Hero";
import About from "@/components/About";
import Gallery from "@/components/Gallery";
import Hours from "@/components/Hours";
import Contact from "@/components/Contact";
import Footer from "@/components/Footer";
import StickyCallCTA from "@/components/StickyCallCTA";
import Reveal from "@/components/Reveal";

/**
 * Section order changed slightly:
 *   Nav → Hero → About → Gallery → Hours → Contact → Footer
 *
 * Hours moved before Contact so the page narrative becomes:
 *   "what is this place" → "what does it look like" → "when is it open" →
 *   "how do I get there / call".
 *
 * StickyCallCTA + Reveal are global client components mounted once at the bottom
 * of the page. Reveal hooks IntersectionObserver to all `.reveal` elements;
 * StickyCallCTA renders the mobile tap-to-call FAB.
 */
export default function Home() {
  return (
    <main className="overflow-x-hidden">
      <Nav />
      <Hero />
      <About />
      {business.photos.gallery.length > 0 && <Gallery />}
      <Hours />
      <Contact />
      <Footer />
      <StickyCallCTA />
      <Reveal />
    </main>
  );
}
