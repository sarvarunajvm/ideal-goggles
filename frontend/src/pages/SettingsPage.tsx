import { useState, useEffect, useCallback } from 'react';
import { apiService, IndexStatus } from '../services/apiClient';
import Navigation from '../components/Navigation';
import StatusBar from '../components/StatusBar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Toaster } from '@/components/ui/toaster';
import { useToast } from '@/components/ui/use-toast';
import {
  FolderOpen,
  Settings2,
  Database,
  Zap,
  Languages,
  Search,
  Plus,
  Trash2,
  Play,
  Square,
  RotateCcw,
  Loader2,
  Image,
  Users,
  FileText,
  Activity
} from 'lucide-react';

interface IndexStats {
  database: {
    total_photos: number;
    indexed_photos: number;
    photos_with_embeddings: number;
    total_faces: number;
  };
}

export default function SettingsPage() {
  const { toast } = useToast();
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [indexStats, setIndexStats] = useState<IndexStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form state
  const [rootFolders, setRootFolders] = useState<string[]>([]);
  const [newFolderPath, setNewFolderPath] = useState('');
  const [ocrLanguages, setOcrLanguages] = useState<string[]>([]);
  const [faceSearchEnabled, setFaceSearchEnabled] = useState(false);
  const [semanticSearchEnabled, setSemanticSearchEnabled] = useState(true);
  const [batchSize, setBatchSize] = useState(50);
  const [thumbnailSize, setThumbnailSize] = useState('medium');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [configData, statusData, statsData] = await Promise.all([
        apiService.getConfig(),
        apiService.getIndexStatus(),
        apiService.getIndexStats(),
      ]);

      setIndexStatus(statusData);
      setIndexStats(statsData as unknown as IndexStats);

      // Update form state
      setRootFolders(configData.roots || []);
      setOcrLanguages(configData.ocr_languages || []);
      setFaceSearchEnabled(configData.face_search_enabled || false);
      setSemanticSearchEnabled(configData.semantic_search_enabled !== false);
      setBatchSize(configData.batch_size || 50);
      setThumbnailSize(configData.thumbnail_size || 'medium');
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : 'Failed to load configuration',
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const saveConfig = async () => {
    try {
      setSaving(true);

      // Update root folders
      await apiService.updateRoots(rootFolders);

      // Update other config
      await apiService.updateConfig({
        ocr_languages: ocrLanguages,
        face_search_enabled: faceSearchEnabled,
        semantic_search_enabled: semanticSearchEnabled,
        batch_size: batchSize,
        thumbnail_size: thumbnailSize,
      });

      toast({
        title: "Success",
        description: "Configuration saved successfully!",
      });

      // Reload data
      await loadData();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : 'Failed to save configuration',
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const addRootFolder = () => {
    if (newFolderPath.trim() && !rootFolders.includes(newFolderPath.trim())) {
      setRootFolders([...rootFolders, newFolderPath.trim()]);
      setNewFolderPath('');
    }
  };

  const removeRootFolder = (index: number) => {
    setRootFolders(rootFolders.filter((_, i) => i !== index));
  };

  const startIndexing = async (full = false) => {
    try {
      await apiService.startIndexing(full);
      toast({
        title: "Success",
        description: `${full ? 'Full' : 'Incremental'} indexing started!`,
      });
      // Reload status
      await loadData();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : 'Failed to start indexing',
        variant: "destructive",
      });
    }
  };

  const stopIndexing = async () => {
    try {
      await apiService.stopIndexing();
      toast({
        title: "Success",
        description: "Indexing stopped!",
      });
      // Reload status
      await loadData();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : 'Failed to stop indexing',
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-background">
        <Navigation />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
            <p className="text-muted-foreground">Loading settings...</p>
          </div>
        </div>
        <StatusBar />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      <Navigation />

      <div className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-center space-x-3 mb-8">
            <Settings2 className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Settings</h1>
          </div>

          <Tabs defaultValue="storage" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="storage" className="flex items-center space-x-2">
                <Database className="h-4 w-4" />
                <span>Storage & Indexing</span>
              </TabsTrigger>
              <TabsTrigger value="features" className="flex items-center space-x-2">
                <Search className="h-4 w-4" />
                <span>Search Features</span>
              </TabsTrigger>
              <TabsTrigger value="status" className="flex items-center space-x-2">
                <Activity className="h-4 w-4" />
                <span>System Status</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="storage" className="space-y-6">
              {/* Root Folders Section */}
              <Card className="transition-all duration-200 hover:shadow-md">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <FolderOpen className="h-5 w-5 text-blue-600" />
                    <span>Photo Directories</span>
                  </CardTitle>
                  <CardDescription>
                    Configure which folders to scan for photos. The system will recursively search these directories.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Current Folders */}
                  <div className="space-y-2">
                    {rootFolders.map((folder, index) => (
                      <div key={index} className="group flex items-center justify-between p-3 bg-muted/50 rounded-lg border transition-all duration-200 hover:bg-muted">
                        <span className="font-mono text-sm flex-1 truncate">{folder}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeRootFolder(index)}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>

                  {/* Add New Folder */}
                  <div className="flex space-x-2">
                    <Input
                      value={newFolderPath}
                      onChange={(e) => setNewFolderPath(e.target.value)}
                      placeholder="/path/to/your/photos"
                      className="flex-1"
                    />
                    <Button
                      onClick={addRootFolder}
                      disabled={!newFolderPath.trim()}
                      className="flex items-center space-x-2"
                    >
                      <Plus className="h-4 w-4" />
                      <span>Add</span>
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Indexing Controls */}
              <Card className="transition-all duration-200 hover:shadow-md">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Zap className="h-5 w-5 text-orange-600" />
                    <span>Indexing Controls</span>
                  </CardTitle>
                  <CardDescription>
                    Manage photo indexing and processing operations.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Current Status */}
                  {indexStatus && (
                    <div className="p-4 border rounded-lg bg-card">
                      <div className="flex items-center justify-between mb-3">
                        <Label className="font-medium">Current Status</Label>
                        <Badge
                          variant={
                            indexStatus.status === 'indexing' ? 'default' :
                            indexStatus.status === 'error' ? 'destructive' :
                            'secondary'
                          }
                          className="capitalize"
                        >
                          {indexStatus.status}
                        </Badge>
                      </div>

                      {indexStatus.status === 'indexing' && (
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            Phase: <span className="font-medium">{indexStatus.progress.current_phase}</span>
                          </div>
                          {indexStatus.progress.total_files > 0 && (
                            <div className="space-y-1">
                              <div className="flex justify-between text-sm">
                                <span>Progress</span>
                                <span>{indexStatus.progress.processed_files}/{indexStatus.progress.total_files} files</span>
                              </div>
                              <Progress
                                value={(indexStatus.progress.processed_files / indexStatus.progress.total_files) * 100}
                                className="h-2"
                              />
                            </div>
                          )}
                        </div>
                      )}

                      {indexStatus.errors.length > 0 && (
                        <div className="mt-3 p-3 bg-destructive/5 border border-destructive/20 rounded-md">
                          <details className="text-sm">
                            <summary className="text-destructive cursor-pointer font-medium">
                              {indexStatus.errors.length} error(s) encountered
                            </summary>
                            <div className="mt-2 space-y-1 max-h-24 overflow-y-auto">
                              {indexStatus.errors.map((error: string, index: number) => (
                                <div key={index} className="text-destructive font-mono text-xs p-1 bg-background rounded">
                                  {error}
                                </div>
                              ))}
                            </div>
                          </details>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Index Actions */}
                  <div className="flex flex-wrap gap-3">
                    <Button
                      onClick={() => startIndexing(false)}
                      disabled={indexStatus?.status === 'indexing'}
                      className="flex items-center space-x-2"
                    >
                      <Play className="h-4 w-4" />
                      <span>Start Incremental</span>
                    </Button>
                    <Button
                      onClick={() => startIndexing(true)}
                      disabled={indexStatus?.status === 'indexing'}
                      variant="secondary"
                      className="flex items-center space-x-2"
                    >
                      <RotateCcw className="h-4 w-4" />
                      <span>Full Re-Index</span>
                    </Button>
                    {indexStatus?.status === 'indexing' && (
                      <Button
                        onClick={stopIndexing}
                        variant="destructive"
                        className="flex items-center space-x-2"
                      >
                        <Square className="h-4 w-4" />
                        <span>Stop</span>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="features" className="space-y-6">
              {/* Advanced Features */}
              <Card className="transition-all duration-200 hover:shadow-md">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Languages className="h-5 w-5 text-purple-600" />
                    <span>OCR Languages</span>
                  </CardTitle>
                  <CardDescription>
                    Select languages for text extraction from images (requires Tesseract).
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {[
                      { code: 'eng', name: 'English' },
                      { code: 'tam', name: 'Tamil' }
                    ].map(({ code, name }) => (
                      <div key={code} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-muted/50 transition-colors">
                        <Checkbox
                          id={`ocr-${code}`}
                          checked={ocrLanguages.includes(code)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setOcrLanguages([...ocrLanguages, code]);
                            } else {
                              setOcrLanguages(ocrLanguages.filter(l => l !== code));
                            }
                          }}
                        />
                        <Label htmlFor={`ocr-${code}`} className="font-medium cursor-pointer">
                          {name}
                        </Label>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Semantic Search */}
              <Card className="transition-all duration-200 hover:shadow-md">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Search className="h-5 w-5 text-blue-600" />
                    <span>Semantic Search</span>
                  </CardTitle>
                  <CardDescription>
                    Enable AI-powered semantic search capabilities.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <Label htmlFor="semantic-search" className="font-medium">Enable Semantic Search</Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Use AI embeddings for natural language photo search.
                      </p>
                    </div>
                    <Switch
                      id="semantic-search"
                      checked={semanticSearchEnabled}
                      onCheckedChange={setSemanticSearchEnabled}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Face Search */}
              <Card className="transition-all duration-200 hover:shadow-md">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-green-600" />
                    <span>Face Recognition</span>
                  </CardTitle>
                  <CardDescription>
                    Enable face detection and recognition capabilities.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <Label htmlFor="face-search" className="font-medium">Enable Face Search</Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Detect and recognize faces in photos (requires additional dependencies).
                      </p>
                    </div>
                    <Switch
                      id="face-search"
                      checked={faceSearchEnabled}
                      onCheckedChange={setFaceSearchEnabled}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Processing Settings */}
              <Card className="transition-all duration-200 hover:shadow-md">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Settings2 className="h-5 w-5 text-purple-600" />
                    <span>Processing Settings</span>
                  </CardTitle>
                  <CardDescription>
                    Configure batch processing and thumbnail generation.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Batch Size */}
                  <div className="space-y-2">
                    <Label htmlFor="batch-size" className="font-medium">Batch Size</Label>
                    <div className="flex items-center space-x-3">
                      <Input
                        id="batch-size"
                        type="number"
                        min="1"
                        max="500"
                        value={batchSize}
                        onChange={(e) => setBatchSize(parseInt(e.target.value) || 50)}
                        className="w-32"
                      />
                      <span className="text-sm text-muted-foreground">photos per batch</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Number of photos to process in each batch during indexing.
                    </p>
                  </div>

                  {/* Thumbnail Size */}
                  <div className="space-y-2">
                    <Label htmlFor="thumbnail-size" className="font-medium">Thumbnail Size</Label>
                    <select
                      id="thumbnail-size"
                      value={thumbnailSize}
                      onChange={(e) => setThumbnailSize(e.target.value)}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option value="small">Small (150x150)</option>
                      <option value="medium">Medium (300x300)</option>
                      <option value="large">Large (600x600)</option>
                    </select>
                    <p className="text-sm text-muted-foreground">
                      Size of generated thumbnails for photo previews.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="status" className="space-y-6">
              {/* Database Statistics */}
              {indexStats && (
                <Card className="transition-all duration-200 hover:shadow-md">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Database className="h-5 w-5 text-blue-600" />
                      <span>Database Statistics</span>
                    </CardTitle>
                    <CardDescription>
                      Overview of your photo library and indexing progress.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-4 border rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 transition-all duration-200 hover:shadow-sm">
                        <Image className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                        <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                          {indexStats.database.total_photos.toLocaleString()}
                        </div>
                        <div className="text-sm text-blue-600 dark:text-blue-400">Total Photos</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 transition-all duration-200 hover:shadow-sm">
                        <FileText className="h-8 w-8 mx-auto mb-2 text-green-600" />
                        <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                          {indexStats.database.indexed_photos.toLocaleString()}
                        </div>
                        <div className="text-sm text-green-600 dark:text-green-400">Indexed</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 transition-all duration-200 hover:shadow-sm">
                        <Search className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                        <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                          {indexStats.database.photos_with_embeddings.toLocaleString()}
                        </div>
                        <div className="text-sm text-purple-600 dark:text-purple-400">With Embeddings</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900 transition-all duration-200 hover:shadow-sm">
                        <Users className="h-8 w-8 mx-auto mb-2 text-orange-600" />
                        <div className="text-2xl font-bold text-orange-700 dark:text-orange-300">
                          {indexStats.database.total_faces.toLocaleString()}
                        </div>
                        <div className="text-sm text-orange-600 dark:text-orange-400">Faces Detected</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Save Configuration */}
            <div className="flex justify-end pt-6 border-t">
              <Button
                onClick={saveConfig}
                disabled={saving}
                className="px-8 py-3 text-base font-medium"
              >
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Settings2 className="mr-2 h-4 w-4" />
                    Save Configuration
                  </>
                )}
              </Button>
            </div>
          </Tabs>
        </div>
      </div>

      <StatusBar />
      <Toaster />
    </div>
  );
}