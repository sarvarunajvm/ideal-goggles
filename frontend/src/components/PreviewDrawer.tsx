import { useState, useEffect } from 'react';
import { SearchResult } from '../services/apiClient';

interface PreviewDrawerProps {
  item: SearchResult | null;
  isOpen: boolean;
  onClose: () => void;
  onRevealInFolder?: (item: SearchResult) => void;
  onNext?: () => void;
  onPrevious?: () => void;
}

export default function PreviewDrawer({
  item,
  isOpen,
  onClose,
  onRevealInFolder,
  onNext,
  onPrevious
}: PreviewDrawerProps) {
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    setImageError(false);
  }, [item]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowRight':
          onNext?.();
          break;
        case 'ArrowLeft':
          onPrevious?.();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onNext, onPrevious]);

  if (!isOpen || !item) return null;

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return 'Unknown';
    }
  };

  const getBadgeColor = (badge: string) => {
    const colors: Record<string, string> = {
      'OCR': 'bg-blue-100 text-blue-800',
      'Face': 'bg-red-100 text-red-800',
      'Photo-Match': 'bg-indigo-100 text-indigo-800',
      'EXIF': 'bg-orange-100 text-orange-800',
      'filename': 'bg-green-100 text-green-800',
      'folder': 'bg-purple-100 text-purple-800',
    };
    return colors[badge] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] w-full mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 truncate" title={item.filename}>
            {item.filename}
          </h2>
          <div className="flex items-center space-x-2">
            {onPrevious && (
              <button
                onClick={onPrevious}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                title="Previous photo (←)"
              >
                ←
              </button>
            )}
            {onNext && (
              <button
                onClick={onNext}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                title="Next photo (→)"
              >
                →
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              title="Close (Esc)"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Image Preview */}
          <div className="flex-1 flex items-center justify-center bg-gray-50 p-4">
            {!imageError && item.thumb_path ? (
              <img
                src={`http://localhost:8000${item.thumb_path}`}
                alt={item.filename}
                className="max-w-full max-h-full object-contain"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="flex flex-col items-center text-gray-400">
                <div className="text-8xl mb-4">📷</div>
                <p className="text-lg">Preview not available</p>
              </div>
            )}
          </div>

          {/* Sidebar with details */}
          <div className="w-80 border-l border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4 space-y-6">
              {/* Basic Info */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">File Information</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">Path:</span>
                    <p className="text-gray-900 break-all">{item.path}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Folder:</span>
                    <p className="text-gray-900 break-all">{item.folder}</p>
                  </div>
                  {item.shot_dt && (
                    <div>
                      <span className="text-gray-500">Date Taken:</span>
                      <p className="text-gray-900">{formatTimestamp(item.shot_dt)}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-gray-500">Relevance Score:</span>
                    <p className="text-gray-900">{(item.score * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>

              {/* Badges */}
              {item.badges.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Match Types</h3>
                  <div className="flex flex-wrap gap-2">
                    {item.badges.map((badge, index) => (
                      <span
                        key={index}
                        className={`px-3 py-1 text-sm rounded-full ${getBadgeColor(badge)}`}
                      >
                        {badge}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Snippet */}
              {item.snippet && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Text Match</h3>
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">"{item.snippet}"</p>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Actions</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => onRevealInFolder?.(item)}
                    className="w-full px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <span>📁</span>
                    <span>Reveal in Folder</span>
                  </button>

                  <button
                    onClick={() => navigator.clipboard.writeText(item.path)}
                    className="w-full px-4 py-2 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <span>📋</span>
                    <span>Copy File Path</span>
                  </button>

                  <button
                    onClick={() => {
                      // Open original image in default viewer
                      window.open(`file://${item.path}`, '_blank');
                    }}
                    className="w-full px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <span>👁️</span>
                    <span>Open in Viewer</span>
                  </button>
                </div>
              </div>

              {/* Keyboard shortcuts help */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Keyboard Shortcuts</h3>
                <div className="text-xs text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Next photo:</span>
                    <span className="font-mono bg-gray-200 px-1 rounded">→</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Previous photo:</span>
                    <span className="font-mono bg-gray-200 px-1 rounded">←</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Close:</span>
                    <span className="font-mono bg-gray-200 px-1 rounded">Esc</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}