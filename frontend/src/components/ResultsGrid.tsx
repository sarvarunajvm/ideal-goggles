import { SearchResult } from '../services/apiClient';

interface ResultsGridProps {
  results: SearchResult[];
  onItemClick?: (item: SearchResult) => void;
  onRevealInFolder?: (item: SearchResult) => void;
}

export default function ResultsGrid({ results, onItemClick, onRevealInFolder }: ResultsGridProps) {
  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown';
    try {
      return new Date(timestamp).toLocaleDateString();
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

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔍</div>
        <h2 className="text-2xl font-semibold text-gray-700 mb-2">No photos found</h2>
        <p className="text-gray-500">
          Try a different search term or adjust your filters.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {results.map((item) => (
        <div
          key={item.file_id}
          className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => onItemClick?.(item)}
        >
          {/* Image Preview */}
          <div className="aspect-square bg-gray-100 flex items-center justify-center">
            {item.thumb_path ? (
              <img
                src={`http://localhost:8000${item.thumb_path}`}
                alt={item.filename}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                  (e.target as HTMLImageElement).nextElementSibling!.classList.remove('hidden');
                }}
              />
            ) : null}
            <div className={`text-6xl text-gray-400 ${item.thumb_path ? 'hidden' : ''}`}>
              📷
            </div>
          </div>

          {/* Photo Info */}
          <div className="p-4">
            <h3 className="font-medium text-gray-900 truncate mb-2" title={item.filename}>
              {item.filename}
            </h3>

            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <span>📁</span>
                <span className="truncate" title={item.folder}>
                  {item.folder.replace(/^.*\//, '')}
                </span>
              </div>

              {item.shot_dt && (
                <div className="flex items-center space-x-2">
                  <span>📅</span>
                  <span>{formatTimestamp(item.shot_dt)}</span>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <span>⭐</span>
                <span>Score: {(item.score * 100).toFixed(1)}%</span>
              </div>
            </div>

            {/* Badges */}
            {item.badges.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-3">
                {item.badges.map((badge, index) => (
                  <span
                    key={index}
                    className={`px-2 py-1 text-xs rounded-full ${getBadgeColor(badge)}`}
                  >
                    {badge}
                  </span>
                ))}
              </div>
            )}

            {/* Snippet */}
            {item.snippet && (
              <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm">
                <span className="text-yellow-800">"{item.snippet}"</span>
              </div>
            )}

            {/* Actions */}
            <div className="mt-4 flex space-x-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRevealInFolder?.(item);
                }}
                className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                title="Reveal in folder"
              >
                📁 Reveal
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigator.clipboard.writeText(item.path);
                }}
                className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                title="Copy file path"
              >
                📋 Copy
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}