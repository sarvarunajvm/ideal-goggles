import { useState, useEffect } from 'react';
import { apiService, SearchResult, SearchResponse } from '../services/api';
import SearchBar from '../components/SearchBar';
import SearchResults from '../components/SearchResults';
import SearchFilters from '../components/SearchFilters';
import Navigation from '../components/Navigation';
import StatusBar from '../components/StatusBar';

export default function SearchPage() {
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchMode, setSearchMode] = useState<'text' | 'semantic' | 'image'>('text');

  // Search filters
  const [filters, setFilters] = useState({
    from: '',
    to: '',
    folder: '',
    limit: 50,
  });

  const handleSearch = async (query: string) => {
    if (!query.trim() && searchMode !== 'image') return;

    setLoading(true);
    setError(null);

    try {
      let results: SearchResponse;

      switch (searchMode) {
        case 'text':
          results = await apiService.searchPhotos({
            q: query,
            ...filters,
          });
          break;
        case 'semantic':
          results = await apiService.semanticSearch(query, filters.limit);
          break;
        default:
          throw new Error('Invalid search mode');
      }

      setSearchResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleImageSearch = async (file: File) => {
    setLoading(true);
    setError(null);

    try {
      const results = await apiService.imageSearch(file, filters.limit);
      setSearchResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Image search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters: any) => {
    setFilters({ ...filters, ...newFilters });
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />

      {/* Search Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Photo Search</h1>

          {/* Search Mode Tabs */}
          <div className="flex space-x-1 mb-6">
            {[
              { key: 'text', label: 'Text Search', icon: '🔍' },
              { key: 'semantic', label: 'Semantic Search', icon: '🧠' },
              { key: 'image', label: 'Image Search', icon: '🖼️' },
            ].map((mode) => (
              <button
                key={mode.key}
                onClick={() => setSearchMode(mode.key as any)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  searchMode === mode.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span className="mr-2">{mode.icon}</span>
                {mode.label}
              </button>
            ))}
          </div>

          {/* Search Bar */}
          <SearchBar
            onSearch={handleSearch}
            onImageSearch={handleImageSearch}
            searchMode={searchMode}
            loading={loading}
          />

          {/* Search Filters */}
          <SearchFilters
            filters={filters}
            onChange={handleFilterChange}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full max-w-7xl mx-auto px-6 py-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <div className="text-red-600">
                  <span className="mr-2">⚠️</span>
                  <strong>Error:</strong> {error}
                </div>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="text-gray-600">Searching photos...</span>
              </div>
            </div>
          )}

          {searchResults && !loading && (
            <SearchResults results={searchResults} />
          )}

          {!searchResults && !loading && !error && (
            <div className="flex flex-col items-center justify-center py-20 text-gray-500">
              <div className="text-6xl mb-4">📷</div>
              <h2 className="text-2xl font-semibold mb-2">Search Your Photos</h2>
              <p className="text-lg">
                Enter a search term above to find photos by content, metadata, or visual similarity.
              </p>
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl">
                <div className="text-center p-4">
                  <div className="text-2xl mb-2">🔍</div>
                  <h3 className="font-medium">Text Search</h3>
                  <p className="text-sm">Search by filename, folder, or extracted text</p>
                </div>
                <div className="text-center p-4">
                  <div className="text-2xl mb-2">🧠</div>
                  <h3 className="font-medium">Semantic Search</h3>
                  <p className="text-sm">Describe what you're looking for in natural language</p>
                </div>
                <div className="text-center p-4">
                  <div className="text-2xl mb-2">🖼️</div>
                  <h3 className="font-medium">Image Search</h3>
                  <p className="text-sm">Upload an image to find visually similar photos</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Status Bar */}
      <StatusBar />
    </div>
  );
}