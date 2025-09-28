import { useState } from 'react';
import { apiService, SearchResponse, SearchResult } from '../services/apiClient';
import Navigation from '../components/Navigation';
import StatusBar from '../components/StatusBar';
import PreviewDrawer from '../components/PreviewDrawer';
import { osIntegration } from '../services/osIntegration';

// shadcn/ui components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';

// Icons
import {
  Search,
  Brain,
  Image as ImageIcon,
  Upload,
  Filter,
  Calendar,
  Folder,
  Clock,
  FileText,
  ExternalLink,
  AlertCircle
} from 'lucide-react';

// Modern Search Bar Component
function ModernSearchBar({
  onSearch,
  onImageSearch,
  searchMode,
  loading
}: {
  onSearch: (query: string) => void;
  onImageSearch: (file: File) => void;
  searchMode: 'text' | 'semantic' | 'image';
  loading: boolean;
}) {
  const [query, setQuery] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && searchMode !== 'image') {
      onSearch(query.trim());
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find(file => file.type.startsWith('image/'));

    if (imageFile && searchMode === 'image') {
      onImageSearch(imageFile);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && searchMode === 'image') {
      onImageSearch(file);
    }
  };

  return (
    <div className="space-y-4">
      {searchMode === 'image' ? (
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          }`}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            setDragActive(false);
          }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="image/*"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={loading}
          />
          <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">Upload an image to search</h3>
          <p className="text-sm text-muted-foreground">
            Drag and drop an image here, or click to select
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                searchMode === 'semantic'
                  ? "Describe what you're looking for..."
                  : "Search photos by filename, folder, or content..."
              }
              className="pl-10 h-12 text-base"
              disabled={loading}
            />
          </div>
          <Button
            type="submit"
            size="lg"
            disabled={loading || !query.trim()}
            className="px-8"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Search
              </>
            )}
          </Button>
        </form>
      )}
    </div>
  );
}

// Loading Skeleton Grid
function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: 12 }).map((_, i) => (
        <Card key={i} className="overflow-hidden">
          <Skeleton className="aspect-square w-full" />
          <CardContent className="p-4">
            <Skeleton className="h-4 w-3/4 mb-2" />
            <Skeleton className="h-3 w-1/2" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Modern Results Grid
function ModernResultsGrid({
  results,
  onItemClick,
  onRevealInFolder
}: {
  results: SearchResult[];
  onItemClick: (item: SearchResult) => void;
  onRevealInFolder: (item: SearchResult) => void;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {results.map((item) => (
        <Card
          key={item.file_id}
          className="group overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:-translate-y-1"
          onClick={() => onItemClick(item)}
        >
          <div className="relative aspect-square overflow-hidden">
            {item.thumb_path ? (
              <img
                src={`file://${item.thumb_path}`}
                alt={item.filename}
                className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-110"
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full bg-muted flex items-center justify-center">
                <ImageIcon className="h-8 w-8 text-muted-foreground" />
              </div>
            )}

            {/* Overlay with actions */}
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200">
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <Button
                  size="icon"
                  variant="secondary"
                  className="h-8 w-8 backdrop-blur-sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRevealInFolder(item);
                  }}
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Score badge */}
            {item.score && (
              <div className="absolute top-2 left-2">
                <Badge variant="secondary" className="backdrop-blur-sm">
                  {(item.score * 100).toFixed(0)}%
                </Badge>
              </div>
            )}
          </div>

          <CardContent className="p-4">
            <h3 className="font-medium text-sm mb-2 truncate" title={item.filename}>
              {item.filename}
            </h3>

            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
              <Folder className="h-3 w-3" />
              <span className="truncate flex-1">{item.folder || 'Unknown'}</span>
            </div>

            {item.shot_dt && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                <Calendar className="h-3 w-3" />
                <span>{new Date(item.shot_dt).toLocaleDateString()}</span>
              </div>
            )}

            {/* Tags */}
            {item.badges && item.badges.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {item.badges.slice(0, 2).map((badge, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {badge}
                  </Badge>
                ))}
                {item.badges.length > 2 && (
                  <Badge variant="outline" className="text-xs">
                    +{item.badges.length - 2}
                  </Badge>
                )}
              </div>
            )}
            {item.snippet && (
              <div className="flex items-center gap-1 mt-2">
                <Badge variant="outline" className="text-xs">
                  <FileText className="h-2 w-2 mr-1" />
                  Text
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function SearchPage() {
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchMode, setSearchMode] = useState<'text' | 'semantic' | 'image'>('text');
  const [selectedItem, setSelectedItem] = useState<SearchResult | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

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

  const handleFilterChange = (newFilters: Partial<typeof filters>) => {
    setFilters({ ...filters, ...newFilters });
  };

  const handleItemClick = (item: SearchResult) => {
    setSelectedItem(item);
    setPreviewOpen(true);
  };

  const handleRevealInFolder = async (item: SearchResult) => {
    try {
      await osIntegration.revealInFolder(item.path);
    } catch (error) {
      // Silent failure - error will be handled by osIntegration service
    }
  };

  const handleNextItem = () => {
    if (!searchResults || !selectedItem) return;
    const currentIndex = searchResults.items.findIndex(item => item.file_id === selectedItem.file_id);
    const nextIndex = (currentIndex + 1) % searchResults.items.length;
    setSelectedItem(searchResults.items[nextIndex]);
  };

  const handlePreviousItem = () => {
    if (!searchResults || !selectedItem) return;
    const currentIndex = searchResults.items.findIndex(item => item.file_id === selectedItem.file_id);
    const prevIndex = (currentIndex - 1 + searchResults.items.length) % searchResults.items.length;
    setSelectedItem(searchResults.items[prevIndex]);
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Navigation */}
      <Navigation />

      {/* Search Header */}
      <div className="bg-card shadow-sm border-b p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Search Mode Tabs */}
          <Tabs value={searchMode} onValueChange={(value) => setSearchMode(value as 'text' | 'semantic' | 'image')}>
            <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
              <TabsTrigger value="text" className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                Text Search
              </TabsTrigger>
              <TabsTrigger value="semantic" className="flex items-center gap-2">
                <Brain className="h-4 w-4" />
                Semantic
              </TabsTrigger>
              <TabsTrigger value="image" className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4" />
                Image
              </TabsTrigger>
            </TabsList>

            <TabsContent value={searchMode} className="mt-6">
              <ModernSearchBar
                onSearch={handleSearch}
                onImageSearch={handleImageSearch}
                searchMode={searchMode}
                loading={loading}
              />
            </TabsContent>
          </Tabs>

          {/* Modern Filters */}
          <Card className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Filters:</span>
              </div>

              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <Input
                  type="date"
                  value={filters.from}
                  onChange={(e) => handleFilterChange({ from: e.target.value })}
                  className="w-auto"
                  placeholder="From"
                />
                <span className="text-muted-foreground">to</span>
                <Input
                  type="date"
                  value={filters.to}
                  onChange={(e) => handleFilterChange({ to: e.target.value })}
                  className="w-auto"
                  placeholder="To"
                />
              </div>

              <div className="flex items-center gap-2">
                <Folder className="h-4 w-4 text-muted-foreground" />
                <Input
                  value={filters.folder}
                  onChange={(e) => handleFilterChange({ folder: e.target.value })}
                  placeholder="Folder path..."
                  className="w-48"
                />
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Limit:</span>
                <Input
                  type="number"
                  value={filters.limit}
                  onChange={(e) => handleFilterChange({ limit: parseInt(e.target.value) || 50 })}
                  min="1"
                  max="1000"
                  className="w-20"
                />
              </div>

              {(filters.from || filters.to || filters.folder) && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilters({ from: '', to: '', folder: '', limit: 50 })}
                >
                  Clear Filters
                </Button>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
            {/* Error State */}
            {error && (
              <Card className="border-destructive/50 bg-destructive/5">
                <CardContent className="flex items-center gap-3 p-4">
                  <AlertCircle className="h-5 w-5 text-destructive" />
                  <div>
                    <h3 className="font-medium text-destructive">Search Error</h3>
                    <p className="text-sm text-muted-foreground">{error}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Loading State */}
            {loading && <SkeletonGrid />}

            {/* Results */}
            {searchResults && !loading && (
              <div className="space-y-6">
                {/* Results Header */}
                <Card className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <h2 className="text-2xl font-semibold tracking-tight">
                        {searchResults.total_matches.toLocaleString()} photo{searchResults.total_matches !== 1 ? 's' : ''} found
                      </h2>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Search className="h-4 w-4" />
                          <span>"{searchResults.query}"</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>{searchResults.took_ms}ms</span>
                        </div>
                      </div>
                    </div>
                    <Badge variant="secondary" className="text-sm">
                      {searchMode} search
                    </Badge>
                  </div>
                </Card>

                {/* Results Grid */}
                <ModernResultsGrid
                  results={searchResults.items}
                  onItemClick={handleItemClick}
                  onRevealInFolder={handleRevealInFolder}
                />
              </div>
            )}

            {/* Empty State */}
            {!searchResults && !loading && !error && (
              <div className="flex flex-col items-center justify-center py-20">
                <div className="text-center space-y-6 max-w-2xl">
                  <ImageIcon className="mx-auto h-24 w-24 text-muted-foreground/50" />
                  <div className="space-y-2">
                    <h2 className="text-3xl font-bold tracking-tight">Search Your Photos</h2>
                    <p className="text-lg text-muted-foreground">
                      Enter a search term above to find photos by content, metadata, or visual similarity.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
                    <Card className="p-6 text-center hover:shadow-md transition-shadow">
                      <Search className="mx-auto h-12 w-12 text-primary mb-4" />
                      <h3 className="font-semibold mb-2">Text Search</h3>
                      <p className="text-sm text-muted-foreground">
                        Search by filename, folder, or extracted text
                      </p>
                    </Card>

                    <Card className="p-6 text-center hover:shadow-md transition-shadow">
                      <Brain className="mx-auto h-12 w-12 text-primary mb-4" />
                      <h3 className="font-semibold mb-2">Semantic Search</h3>
                      <p className="text-sm text-muted-foreground">
                        Describe what you're looking for in natural language
                      </p>
                    </Card>

                    <Card className="p-6 text-center hover:shadow-md transition-shadow">
                      <ImageIcon className="mx-auto h-12 w-12 text-primary mb-4" />
                      <h3 className="font-semibold mb-2">Image Search</h3>
                      <p className="text-sm text-muted-foreground">
                        Upload an image to find visually similar photos
                      </p>
                    </Card>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Status Bar */}
      <StatusBar />

      {/* Preview Drawer */}
      <PreviewDrawer
        item={selectedItem}
        isOpen={previewOpen}
        onClose={() => setPreviewOpen(false)}
        onRevealInFolder={handleRevealInFolder}
        onNext={searchResults?.items && searchResults.items.length > 1 ? handleNextItem : undefined}
        onPrevious={searchResults?.items && searchResults.items.length > 1 ? handlePreviousItem : undefined}
      />
    </div>
  );
}