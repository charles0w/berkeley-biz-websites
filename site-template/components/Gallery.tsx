import { business } from "@/lib/business";

// Gallery — asymmetric bento grid with photo-warm filter.
//
// Differs from the previous template:
//  - Uses <img> instead of background-image divs so object-cover + aspect-*
//    work properly. Photos sit inside warm cards with subtle ambient shadows
//    instead of edge-bleed bg-stone-200 blocks.
//  - photo-warm filter (saturate 0.88, contrast 1.04, sepia 0.06) gives every
//    photo a coherent magazine treatment that hides the variance in raw
//    Google Maps user-photo quality.
//  - Aspect ratios shift per layout instead of fixed h-[60vh].
//  - Now supports up to 4 photos.

export default function Gallery() {
  const photos = business.photos.gallery.slice(0, 4);
  if (photos.length === 0) return null;

  return (
    <section id="gallery" className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 py-20 md:py-28">
      <div className="grid grid-cols-12 gap-3 md:gap-5">
        {photos.length === 1 && (
          <div className="col-span-12 reveal">
            <div className="aspect-[16/9] bg-paper overflow-hidden shadow-ambient-sm">
              <img
                src={photos[0]}
                alt={`${business.name} photo 1`}
                className="w-full h-full object-cover photo-warm"
                loading="lazy"
                decoding="async"
              />
            </div>
          </div>
        )}

        {photos.length === 2 &&
          photos.map((src, i) => (
            <div key={i} className="col-span-12 md:col-span-6 reveal">
              <div className="aspect-[4/3] bg-paper overflow-hidden shadow-ambient-sm">
                <img
                  src={src}
                  alt={`${business.name} photo ${i + 1}`}
                  className="w-full h-full object-cover photo-warm"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
          ))}

        {photos.length === 3 && (
          <>
            <div className="col-span-12 md:col-span-7 reveal">
              <div className="aspect-[4/3] bg-paper overflow-hidden shadow-ambient-sm">
                <img
                  src={photos[0]}
                  alt={`${business.name} photo 1`}
                  className="w-full h-full object-cover photo-warm"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
            <div className="col-span-6 md:col-span-5 reveal">
              <div className="aspect-square bg-paper overflow-hidden shadow-ambient-sm">
                <img
                  src={photos[1]}
                  alt={`${business.name} photo 2`}
                  className="w-full h-full object-cover photo-warm"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
            <div className="col-span-6 md:col-span-5 reveal">
              <div className="aspect-[4/5] bg-paper overflow-hidden shadow-ambient-sm">
                <img
                  src={photos[2]}
                  alt={`${business.name} photo 3`}
                  className="w-full h-full object-cover photo-warm"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
          </>
        )}

        {photos.length >= 4 && (
          <>
            <div className="col-span-12 md:col-span-7 reveal">
              <div className="aspect-[4/3] bg-paper overflow-hidden shadow-ambient-sm">
                <img
                  src={photos[0]}
                  alt={`${business.name} photo 1`}
                  className="w-full h-full object-cover photo-warm"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
            <div className="col-span-6 md:col-span-5 reveal">
              <div className="aspect-square bg-paper overflow-hidden shadow-ambient-sm">
                <img
                  src={photos[1]}
                  alt={`${business.name} photo 2`}
                  className="w-full h-full object-cover photo-warm"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
            <div className="col-span-6 md:col-span-5 reveal">
              <div className="aspect-[4/5] bg-paper overflow-hidden shadow-ambient-sm">
                <img
                  src={photos[2]}
                  alt={`${business.name} photo 3`}
                  className="w-full h-full object-cover photo-warm"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
            <div className="col-span-12 md:col-span-7 reveal">
              <div className="aspect-[3/2] bg-paper overflow-hidden shadow-ambient-sm">
                <img
                  src={photos[3]}
                  alt={`${business.name} photo 4`}
                  className="w-full h-full object-cover photo-warm"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
