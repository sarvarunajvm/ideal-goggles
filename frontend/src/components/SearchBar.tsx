import { useState, useRef } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onImageSearch: (file: File) => void;
  searchMode: 'text' | 'semantic' | 'image';
  loading: boolean;
}

export default function SearchBar({ onSearch, onImageSearch, searchMode, loading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchMode !== 'image' && query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onImageSearch(file);
    }
  };

  const handleImageUpload = () => {
    fileInputRef.current?.click();
  };

  const placeholderText = {
    text: 'Search by filename, folder, or content...',
    semantic: 'Describe what you\'re looking for (e.g., "sunset over mountains", "people at wedding")...',
    image: 'Click to upload an image for visual similarity search...',
  };

  return (
    <div className="w-full">
      {searchMode === 'image' ? (
        <div
          onClick={handleImageUpload}
          className={`w-full p-4 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
            loading
              ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
          }`}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">📸</div>
            <p className="text-lg font-medium text-gray-700">
              {loading ? 'Processing image...' : 'Upload an image to search'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Click here or drag and drop an image file
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            disabled={loading}
          />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholderText[searchMode]}
              disabled={loading}
              className={`w-full px-4 py-3 pr-12 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                loading ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'
              }`}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 rounded-md transition-colors ${
                loading || !query.trim()
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                '🔍'
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}