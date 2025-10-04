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
        className="absolute left-4 top-1/2 -translate-y-1/2 z-10 rounded-full bg-card/80 backdrop-blur border border-primary/30 p-3 text-primary hover:bg-gradient-to-r hover:from-violet-500 hover:to-purple-500 hover:text-white hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/30 hover:scale-110 transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:bg-card/80 disabled:hover:shadow-none"
        aria-label="Previous photo"
      >
        <ChevronLeft className="h-8 w-8" />
      </button>

      {/* Next button - positioned to not overlap sidebar */}
      <button
        onClick={nextPhoto}
        disabled={!canGoNext}
        className="absolute top-1/2 -translate-y-1/2 z-10 rounded-full bg-card/80 backdrop-blur border border-primary/30 p-3 text-primary hover:bg-gradient-to-r hover:from-violet-500 hover:to-purple-500 hover:text-white hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/30 hover:scale-110 transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:bg-card/80 disabled:hover:shadow-none"
        style={{ right: '21rem' }} // Position it outside the 320px (20rem) sidebar
        aria-label="Next photo"
      >
        <ChevronRight className="h-8 w-8" />
      </button>
    </>
  );
}
