import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LightboxPhoto } from '../../stores/lightboxStore';
import { Loader2 } from 'lucide-react';
import { API_CONFIG } from '../../config/constants';

interface LightboxImageProps {
  photo: LightboxPhoto;
}

export function LightboxImage({ photo }: LightboxImageProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const imageUrl = (() => {
    // If running in Electron (via file protocol) and photo path is available, use direct file access
    // This provides much better performance for high-res images
    if (window.location.protocol === 'file:' && photo.path) {
      // Use standard file:// protocol which Electron supports when reading from renderer
      // (assuming webSecurity is configured to allow it or via standard secure loading)
      return `file://${photo.path}`;
    }

    // Fallback to API for dev mode or when path is missing
    return `/api/photos/${photo.id}/original`;
  })();

  const handleImageLoad = () => {
    setIsLoading(false);
    setHasError(false);
    setErrorMessage('');
  };

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    console.error('Failed to load image:', {
      url: imageUrl,
      photoId: photo.id,
      filename: photo.filename,
      error: e
    });
    
    // If file:// access fails (e.g. security restrictions), try falling back to API
    if (imageUrl.startsWith('file://')) {
        // Use full API URL since relative paths in file:// protocol resolve to filesystem
        const fallbackUrl = `${API_CONFIG.BASE_URL}/photos/${photo.id}/original`;
        if (e.currentTarget.src !== fallbackUrl) {
            console.warn('Falling back to API endpoint...');
            e.currentTarget.src = fallbackUrl;
            return;
        }
    }

    setIsLoading(false);
    setHasError(true);
    setErrorMessage(`Failed to load: ${photo.filename}`);
  };

  // Reset states when photo changes
  useEffect(() => {
    setIsLoading(true);
    setHasError(false);
    setErrorMessage('');
  }, [photo.id]);

  return (
    <div className="relative flex h-full w-full items-center justify-center">
      {/* Loading spinner */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="h-12 w-12 animate-spin text-cyan-400" />
        </div>
      )}

      {/* Error state */}
      {hasError && (
        <div className="text-center">
          <div className="inline-flex flex-col items-center p-8 rounded-lg bg-card/80 backdrop-blur border border-red-500/30">
            <div className="text-6xl mb-4">⚠️</div>
            <p className="text-lg font-medium text-red-400">Unable to load image</p>
            <p className="text-sm mt-2 text-muted-foreground">{errorMessage || photo.filename}</p>
            <p className="text-xs mt-2 text-muted-foreground opacity-60">Photo ID: {photo.id}</p>
          </div>
        </div>
      )}

      {/* Image */}
      {!hasError && (
        <motion.img
          key={photo.id}
          src={imageUrl}
          alt={photo.filename}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          onLoad={handleImageLoad}
          onError={handleImageError}
          className="max-h-full max-w-full object-contain"
          draggable={false}
        />
      )}
    </div>
  );
}
