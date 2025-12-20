import { useLightboxStore } from '../../stores/lightboxStore';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export function LightboxNavigation() {
  const { currentIndex, photos, nextPhoto, prevPhoto } = useLightboxStore();

  const canGoPrev = currentIndex > 0;
  const canGoNext = currentIndex < photos.length - 1;

  if (photos.length <= 1) {
    return null;
  }

  return (
    <>
      {/* Previous button */}
      <button
        onClick={prevPhoto}
        disabled={!canGoPrev}
        className="absolute left-4 top-1/2 -translate-y-1/2 z-10 rounded-full bg-card/80 backdrop-blur border border-primary/30 p-3 text-primary hover:bg-gradient-to-r hover:from-[rgb(var(--purple-rgb))] hover:to-[rgb(var(--purple-rgb))] hover:text-white hover:border-[rgb(var(--purple-rgb))]/50 hover:shadow-[var(--shadow-purple)] hover:scale-110 transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:bg-card/80 disabled:hover:shadow-none"
        aria-label="Previous photo"
        data-testid="lightbox-prev"
      >
        <ChevronLeft className="h-8 w-8" />
      </button>

      {/* Next button - positioned to not overlap sidebar */}
      <button
        onClick={nextPhoto}
        disabled={!canGoNext}
        className="absolute top-1/2 -translate-y-1/2 z-10 rounded-full bg-card/80 backdrop-blur border border-primary/30 p-3 text-primary hover:bg-gradient-to-r hover:from-[rgb(var(--purple-rgb))] hover:to-[rgb(var(--purple-rgb))] hover:text-white hover:border-[rgb(var(--purple-rgb))]/50 hover:shadow-[var(--shadow-purple)] hover:scale-110 transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:bg-card/80 disabled:hover:shadow-none lightbox-next-btn"
        aria-label="Next photo"
        data-testid="lightbox-next"
      >
        <ChevronRight className="h-8 w-8" />
      </button>
    </>
  );
}
