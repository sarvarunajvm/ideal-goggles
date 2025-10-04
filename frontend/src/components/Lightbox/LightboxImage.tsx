import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LightboxPhoto } from '../../stores/lightboxStore';
import { Loader2 } from 'lucide-react';

interface LightboxImageProps {
  photo: LightboxPhoto;
}

export function LightboxImage({ photo }: LightboxImageProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  // In Electron, use file:// protocol for direct access
  // In web dev, use the backend API to serve the original image
  const imageUrl = (() => {
    // For now, always use the API endpoint in development
    // TODO: Re-enable Electron detection when running in Electron
    const photoId = photo.id; // This is already a string
    console.log('Loading image via API:', `/api/photos/${photoId}/original`);
    return `/api/photos/${photoId}/original`;
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
