import { LightboxPhoto } from '../../stores/lightboxStore';
import { osIntegration } from '../../services/osIntegration';
import { Button } from '@/components/ui/button';
import {
  Camera,
  Calendar,
  MapPin,
  FileText,
  Tag,
  Info,
  FolderOpen,
  Copy,
  ExternalLink,
} from 'lucide-react';

interface LightboxMetadataProps {
  photo: LightboxPhoto;
}

interface MetadataRowProps {
  icon: React.ReactNode;
  label: string;
  value: string | number | undefined;
}

function MetadataRow({ icon, label, value }: MetadataRowProps) {
  if (!value) return null;

  return (
    <div className="flex items-start space-x-3 py-2">
      <div className="flex-shrink-0 text-primary">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm text-foreground break-words">{value}</p>
      </div>
    </div>
  );
}

export function LightboxMetadata({ photo }: LightboxMetadataProps) {
  const { metadata } = photo;

  return (
    <div className="h-full w-80 overflow-y-auto bg-card/95 backdrop-blur border-l border-primary/20 p-6 pt-20">
      {/* Photo Details - Combined filename and path */}
      <div className="mb-6 p-4 rounded-lg bg-gradient-to-r from-cyan-400/10 to-teal-400/10 border border-cyan-500/20">
        <div className="flex items-center space-x-2 mb-3">
          <Info className="h-5 w-5 text-cyan-400" />
          <h3 className="font-semibold text-cyan-400">Photo Details</h3>
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Filename</p>
            <p className="text-sm text-foreground break-all font-mono">{photo.filename}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Location</p>
            <p className="text-xs text-foreground break-all font-mono opacity-80">{photo.path}</p>
          </div>
        </div>
      </div>

      {/* Camera info */}
      {(metadata?.camera_make || metadata?.camera_model) && (
        <div className="mb-6">
          <div className="flex items-center space-x-2 mb-3">
            <Camera className="h-5 w-5 text-violet-400" />
            <h3 className="font-semibold text-violet-400">Camera</h3>
          </div>
          <div className="space-y-1 p-3 rounded-lg bg-gradient-to-r from-violet-500/10 to-purple-500/10 border border-violet-500/20">
            {metadata.camera_make && (
              <p className="text-sm text-foreground">{metadata.camera_make}</p>
            )}
            {metadata.camera_model && (
              <p className="text-sm text-muted-foreground">{metadata.camera_model}</p>
            )}
          </div>
        </div>
      )}

      {/* EXIF data */}
      {(metadata?.iso ||
        metadata?.aperture ||
        metadata?.shutter_speed ||
        metadata?.focal_length) && (
        <div className="mb-6">
          <div className="flex items-center space-x-2 mb-3">
            <FileText className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-foreground">Settings</h3>
          </div>
          <div className="space-y-2">
            <MetadataRow
              icon={<span className="text-xs">ISO</span>}
              label="ISO"
              value={metadata.iso}
            />
            <MetadataRow
              icon={<span className="text-xs">f/</span>}
              label="Aperture"
              value={metadata.aperture}
            />
            <MetadataRow
              icon={<span className="text-xs">⏱</span>}
              label="Shutter Speed"
              value={metadata.shutter_speed}
            />
            <MetadataRow
              icon={<span className="text-xs">🔍</span>}
              label="Focal Length"
              value={metadata.focal_length}
            />
          </div>
        </div>
      )}

      {/* Date taken */}
      {metadata?.date_taken && (
        <div className="mb-6">
          <MetadataRow
            icon={<Calendar className="h-5 w-5" />}
            label="Date Taken"
            value={new Date(metadata.date_taken).toLocaleString()}
          />
        </div>
      )}

      {/* Dimensions */}
      {(metadata?.width || metadata?.height) && (
        <div className="mb-6">
          <MetadataRow
            icon={<MapPin className="h-5 w-5" />}
            label="Dimensions"
            value={`${metadata.width} × ${metadata.height}`}
          />
        </div>
      )}

      {/* OCR text */}
      {photo.ocr_text && (
        <div className="mb-6">
          <div className="flex items-center space-x-2 mb-3">
            <FileText className="h-5 w-5 text-amber-400" />
            <h3 className="font-semibold text-amber-400">Extracted Text</h3>
          </div>
          <div className="p-3 rounded-lg bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20">
            <p className="text-sm text-foreground whitespace-pre-wrap font-mono">
              {photo.ocr_text}
            </p>
          </div>
        </div>
      )}

      {/* Tags */}
      {photo.tags && photo.tags.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center space-x-2 mb-3">
            <Tag className="h-5 w-5 text-purple-400" />
            <h3 className="font-semibold text-purple-400">Tags</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {photo.tags.map((tag, index) => {
              // Different gradient colors for different tag types
              const getTagStyle = (tagName: string) => {
                if (tagName.toLowerCase().includes('ocr')) {
                  return 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 border-amber-500/50 text-amber-400';
                } else if (tagName.toLowerCase().includes('face')) {
                  return 'bg-gradient-to-r from-pink-500/20 to-rose-500/20 border-pink-500/50 text-pink-400';
                } else if (tagName.toLowerCase().includes('exif')) {
                  return 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-cyan-500/50 text-cyan-400';
                } else {
                  return 'bg-gradient-to-r from-violet-500/20 to-purple-500/20 border-purple-500/50 text-purple-400';
                }
              };

              return (
                <span
                  key={index}
                  className={`rounded-full px-3 py-1 text-xs font-semibold border ${getTagStyle(tag)}`}
                >
                  {tag}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Keyboard shortcuts */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <Info className="h-5 w-5 text-green-400" />
          <h3 className="font-semibold text-green-400">Shortcuts</h3>
        </div>
        <div className="text-xs text-muted-foreground space-y-1 p-3 rounded-lg bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20">
          <div className="flex justify-between">
            <span>Next photo:</span>
            <span className="font-mono bg-green-500/20 px-2 py-0.5 rounded text-green-400">→</span>
          </div>
          <div className="flex justify-between">
            <span>Previous photo:</span>
            <span className="font-mono bg-green-500/20 px-2 py-0.5 rounded text-green-400">←</span>
          </div>
          <div className="flex justify-between">
            <span>Close:</span>
            <span className="font-mono bg-green-500/20 px-2 py-0.5 rounded text-green-400">Esc</span>
          </div>
        </div>
      </div>

      {/* Actions - Moved to bottom */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <FileText className="h-5 w-5 text-pink-400" />
          <h3 className="font-semibold text-pink-400">Actions</h3>
        </div>
        <div className="space-y-2">
          <Button
            onClick={async () => {
              try {
                await osIntegration.revealInFolder(photo.path);
              } catch (error) {
                console.error('Failed to reveal in folder:', error);
              }
            }}
            variant="outline"
            size="sm"
            className="w-full justify-start border-cyan-500/30 hover:border-cyan-500/50 text-cyan-400 hover:bg-gradient-to-r hover:from-cyan-500/20 hover:to-teal-500/20 hover:text-cyan-300 hover:shadow-lg hover:shadow-cyan-500/20 hover:scale-[1.02] transition-all"
          >
            <FolderOpen className="h-4 w-4 mr-2" />
            Reveal in Folder
          </Button>

          <Button
            onClick={() => {
              navigator.clipboard.writeText(photo.path);
              // You could add a toast notification here
            }}
            variant="outline"
            size="sm"
            className="w-full justify-start border-violet-500/30 hover:border-violet-500/50 text-violet-400 hover:bg-gradient-to-r hover:from-violet-500/20 hover:to-purple-500/20 hover:text-violet-300 hover:shadow-lg hover:shadow-violet-500/20 hover:scale-[1.02] transition-all"
          >
            <Copy className="h-4 w-4 mr-2" />
            Copy File Path
          </Button>

          <Button
            onClick={() => {
              // Open original image in new tab using API endpoint
              const photoId = photo.id;
              window.open(`/api/photos/${photoId}/original`, '_blank');
            }}
            variant="outline"
            size="sm"
            className="w-full justify-start border-amber-500/30 hover:border-amber-500/50 text-amber-400 hover:bg-gradient-to-r hover:from-amber-500/20 hover:to-orange-500/20 hover:text-amber-300 hover:shadow-lg hover:shadow-amber-500/20 hover:scale-[1.02] transition-all"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Open Original
          </Button>
        </div>
      </div>
    </div>
  );
}
