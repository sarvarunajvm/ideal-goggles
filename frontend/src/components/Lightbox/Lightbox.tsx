import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLightboxStore } from '../../stores/lightboxStore';
import { LightboxImage } from './LightboxImage';
import { LightboxNavigation } from './LightboxNavigation';
import { LightboxMetadata } from './LightboxMetadata';
import { X } from 'lucide-react';

export function Lightbox() {
  const { isOpen, currentIndex, photos, closeLightbox, nextPhoto, prevPhoto } =
    useLightboxStore();

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          closeLightbox();
          break;
        case 'ArrowRight':
          nextPhoto();
          break;
        case 'ArrowLeft':
          prevPhoto();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeLightbox, nextPhoto, prevPhoto]);

  // Prevent body scroll when lightbox is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const currentPhoto = photos[currentIndex];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/95 backdrop-blur-sm"
          onClick={closeLightbox}
        >
          {/* Main content area */}
          <div
            className="flex h-full w-full items-center justify-center relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button - positioned to not overlap sidebar */}
            <button
              onClick={closeLightbox}
              className="absolute top-4 right-4 z-20 rounded-full bg-card/95 backdrop-blur border border-primary/30 p-2 text-primary hover:bg-gradient-to-r hover:from-red-500 hover:to-pink-500 hover:text-white hover:border-red-500/50 transition-all shadow-lg hover:shadow-red-500/30 hover:scale-110"
              aria-label="Close lightbox"
              style={{ right: '21rem' }} // Position it outside the 320px (20rem) sidebar
            >
              <X className="h-6 w-6" />
            </button>

            {/* Navigation arrows */}
            <LightboxNavigation />

            {/* Image display */}
            <div className="flex-1 flex items-center justify-center p-4">
              {currentPhoto && <LightboxImage photo={currentPhoto} />}
            </div>

            {/* Metadata sidebar */}
            {currentPhoto && <LightboxMetadata photo={currentPhoto} />}
          </div>

          {/* Photo counter */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-card/95 backdrop-blur border border-primary/30 px-4 py-2 text-sm font-semibold bg-gradient-to-r from-cyan-400/10 to-teal-400/10 text-cyan-400 shadow-lg shadow-cyan-500/20">
            {currentIndex + 1} / {photos.length}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
