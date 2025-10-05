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
      <div className="mb-6 p-4 rounded-lg bg-gradient-to-r from-[rgb(var(--cyan-rgb))]/10 to-[rgb(var(--cyan-rgb))]/15 border border-[rgb(var(--cyan-rgb))]/20 shadow-[var(--shadow-cyan)]">
        <div className="flex items-center space-x-2 mb-3">
          <Info className="h-5 w-5 text-[var(--neon-cyan)]" />
          <h3 className="font-semibold text-[var(--neon-cyan)]">Photo Details</h3>
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
            <Camera className="h-5 w-5 text-[var(--neon-purple)]" />
            <h3 className="font-semibold text-[var(--neon-purple)]">Camera</h3>
          </div>
          <div className="space-y-1 p-3 rounded-lg bg-gradient-to-r from-[rgb(var(--purple-rgb))]/10 to-[rgb(var(--purple-rgb))]/15 border border-[rgb(var(--purple-rgb))]/20 shadow-[var(--shadow-purple)]">
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
            <FileText className="h-5 w-5 text-[var(--gold-primary)]" />
            <h3 className="font-semibold text-[var(--gold-primary)]">Settings</h3>
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
            <FileText className="h-5 w-5 text-[var(--gold-light)]" />
            <h3 className="font-semibold text-[var(--gold-light)]">Extracted Text</h3>
          </div>
          <div className="p-3 rounded-lg bg-gradient-to-r from-[rgb(var(--gold-rgb))]/10 to-[rgb(var(--gold-rgb))]/15 border border-[rgb(var(--gold-rgb))]/20 shadow-[var(--shadow-gold)]">
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
            <Tag className="h-5 w-5 text-[var(--neon-purple)]" />
            <h3 className="font-semibold text-[var(--neon-purple)]">Tags</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {photo.tags.map((tag, index) => {
              // Different gradient colors for different tag types using theme colors
              const getTagStyle = (tagName: string) => {
                if (tagName.toLowerCase().includes('ocr')) {
                  return 'bg-gradient-to-r from-[rgb(var(--gold-rgb))]/20 to-[rgb(var(--gold-rgb))]/30 border-[rgb(var(--gold-rgb))]/50 text-[var(--gold-light)]';
                } else if (tagName.toLowerCase().includes('face')) {
                  return 'bg-gradient-to-r from-[rgb(var(--pink-rgb))]/20 to-[rgb(var(--pink-rgb))]/30 border-[rgb(var(--pink-rgb))]/50 text-[var(--neon-pink)]';
                } else if (tagName.toLowerCase().includes('exif')) {
                  return 'bg-gradient-to-r from-[rgb(var(--cyan-rgb))]/20 to-[rgb(var(--cyan-rgb))]/30 border-[rgb(var(--cyan-rgb))]/50 text-[var(--neon-cyan)]';
                } else {
                  return 'bg-gradient-to-r from-[rgb(var(--purple-rgb))]/20 to-[rgb(var(--purple-rgb))]/30 border-[rgb(var(--purple-rgb))]/50 text-[var(--neon-purple)]';
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
          <Info className="h-5 w-5 text-[var(--neon-green)]" />
          <h3 className="font-semibold text-[var(--neon-green)]">Shortcuts</h3>
        </div>
        <div className="text-xs text-muted-foreground space-y-1 p-3 rounded-lg bg-gradient-to-r from-[rgb(var(--green-rgb))]/10 to-[rgb(var(--green-rgb))]/15 border border-[rgb(var(--green-rgb))]/20 shadow-[var(--shadow-green)]">
          <div className="flex justify-between">
            <span>Next photo:</span>
            <span className="font-mono bg-[rgb(var(--green-rgb))]/20 px-2 py-0.5 rounded text-[var(--neon-green)]">→</span>
          </div>
          <div className="flex justify-between">
            <span>Previous photo:</span>
            <span className="font-mono bg-[rgb(var(--green-rgb))]/20 px-2 py-0.5 rounded text-[var(--neon-green)]">←</span>
          </div>
          <div className="flex justify-between">
            <span>Close:</span>
            <span className="font-mono bg-[rgb(var(--green-rgb))]/20 px-2 py-0.5 rounded text-[var(--neon-green)]">Esc</span>
          </div>
        </div>
      </div>

      {/* Actions - Moved to bottom */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <FileText className="h-5 w-5 text-[var(--neon-pink)]" />
          <h3 className="font-semibold text-[var(--neon-pink)]">Actions</h3>
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
            className="w-full justify-start border-[rgb(var(--cyan-rgb))]/30 hover:border-[rgb(var(--cyan-rgb))]/50 text-[var(--neon-cyan)] hover:bg-gradient-to-r hover:from-[rgb(var(--cyan-rgb))]/20 hover:to-[rgb(var(--cyan-rgb))]/30 hover:text-[var(--neon-cyan)] hover:shadow-[var(--shadow-cyan)] hover:scale-[1.02] transition-all"
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
            className="w-full justify-start border-[rgb(var(--purple-rgb))]/30 hover:border-[rgb(var(--purple-rgb))]/50 text-[var(--neon-purple)] hover:bg-gradient-to-r hover:from-[rgb(var(--purple-rgb))]/20 hover:to-[rgb(var(--purple-rgb))]/30 hover:text-[var(--neon-purple)] hover:shadow-[var(--shadow-purple)] hover:scale-[1.02] transition-all"
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
            className="w-full justify-start border-[rgb(var(--gold-rgb))]/30 hover:border-[rgb(var(--gold-rgb))]/50 text-[var(--gold-light)] hover:bg-gradient-to-r hover:from-[rgb(var(--gold-rgb))]/20 hover:to-[rgb(var(--gold-rgb))]/30 hover:text-[var(--gold-light)] hover:shadow-[var(--shadow-gold)] hover:scale-[1.02] transition-all"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Open Original
          </Button>
        </div>
      </div>
    </div>
  );
}
