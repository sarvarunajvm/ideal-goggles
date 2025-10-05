import { useState, useEffect, useCallback, useRef } from 'react'
import { apiService, IndexStatus, DependenciesResponse } from '../services/apiClient'
import { useOnboardingStore } from '../stores/onboardingStore'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Toaster } from '@/components/ui/toaster'
import { useToast } from '@/components/ui/use-toast'
import { FolderOpen, FolderPlus, Settings2, Trash2, Play, Square, RotateCcw, Loader2, Zap } from 'lucide-react'


export default function SettingsPage() {
  const { toast } = useToast()
  const { reset: resetOnboarding } = useOnboardingStore()
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [dependencies, setDependencies] = useState<DependenciesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Form state
  const [rootFolders, setRootFolders] = useState<string[]>([])
  const [ocrEnabled, setOcrEnabled] = useState(false)
  const [ocrLanguages, setOcrLanguages] = useState<string[]>([])
  const [faceSearchEnabled, setFaceSearchEnabled] = useState(false)
  const [semanticSearchEnabled, setSemanticSearchEnabled] = useState(true)
  // Reserved for future config surface
  // const [batchSize, setBatchSize] = useState(50)
  // const [thumbnailSize, setThumbnailSize] = useState('medium')

  // Debounce timer ref
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const initialLoadRef = useRef(true)

  // Check if OCR is available based on dependencies
  const isOcrAvailable = dependencies?.features?.text_recognition ?? false

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const [configData, statusData, dependenciesData] = await Promise.all([
        apiService.getConfig(),
        apiService.getIndexStatus(),
        apiService.getDependencies(),
      ])

      setIndexStatus(statusData)
      setDependencies(dependenciesData)

      // Update form state
      setRootFolders(configData.roots || [])
      setOcrEnabled(configData.ocr_enabled || false)
      setOcrLanguages(configData.ocr_languages || [])
      setFaceSearchEnabled(configData.face_search_enabled || false)
      setSemanticSearchEnabled(configData.semantic_search_enabled !== false)
      // setBatchSize(configData.batch_size || 50)
      // setThumbnailSize(configData.thumbnail_size || 'medium')

      initialLoadRef.current = false
    } catch (err) {
      toast({
        title: 'Error',
        description:
          err instanceof Error ? err.message : 'Failed to load configuration',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Auto-save functionality
  const saveConfig = async (configUpdate: any, updateType: 'roots' | 'config' = 'config') => {
    if (initialLoadRef.current) return // Don't save during initial load

    try {
      setSaving(true)

      if (updateType === 'roots') {
        await apiService.updateRoots(configUpdate)
      } else {
        await apiService.updateConfig(configUpdate)
      }
    } catch (err) {
      toast({
        title: 'Error',
        description:
          err instanceof Error ? err.message : 'Failed to save configuration',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  // Auto-save with debouncing
  const debouncedSave = useCallback((configUpdate: any, updateType: 'roots' | 'config' = 'config') => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
    }
    saveTimerRef.current = setTimeout(() => {
      saveConfig(configUpdate, updateType)
    }, 1000) // 1 second debounce
  }, [])

  // Auto-save hooks
  useEffect(() => {
    if (!initialLoadRef.current) {
      debouncedSave(rootFolders, 'roots')
    }
  }, [rootFolders])

  useEffect(() => {
    if (!initialLoadRef.current) {
      debouncedSave({ ocr_enabled: ocrEnabled }, 'config')
    }
  }, [ocrEnabled])

  useEffect(() => {
    if (!initialLoadRef.current && ocrEnabled) {
      debouncedSave({ ocr_languages: ocrLanguages }, 'config')
    }
  }, [ocrLanguages])

  useEffect(() => {
    if (!initialLoadRef.current) {
      debouncedSave({ face_search_enabled: faceSearchEnabled }, 'config')
    }
  }, [faceSearchEnabled])

  useEffect(() => {
    if (!initialLoadRef.current) {
      debouncedSave({ semantic_search_enabled: semanticSearchEnabled }, 'config')
    }
  }, [semanticSearchEnabled])

  const addRootFolder = async () => {
    try {
      if (window.electronAPI?.selectDirectory) {
        const result = await window.electronAPI.selectDirectory()
        if (result && !result.canceled && result.filePaths.length > 0) {
          const folderPath = result.filePaths[0]
          if (!rootFolders.includes(folderPath)) {
            setRootFolders([...rootFolders, folderPath])
          }
        }
      } else {
        const folderPath = prompt('Enter the folder path:')
        if (folderPath && !rootFolders.includes(folderPath)) {
          setRootFolders([...rootFolders, folderPath])
        }
      }
    } catch (error) {
      console.error('Failed to select folder:', error)
      toast({
        title: 'Error',
        description: 'Failed to select folder. Please try again.',
        variant: 'destructive',
      })
    }
  }

  const removeRootFolder = (index: number) => {
    setRootFolders(rootFolders.filter((_, i) => i !== index))
  }

  const startIndexing = async (full = false) => {
    try {
      await apiService.startIndexing(full)
      toast({
        title: 'Success',
        description: `${full ? 'Full' : 'Quick'} indexing started!`,
      })
      await loadData()
    } catch (err) {
      toast({
        title: 'Error',
        description:
          err instanceof Error ? err.message : 'Failed to start indexing',
        variant: 'destructive',
      })
    }
  }

  const stopIndexing = async () => {
    try {
      await apiService.stopIndexing()
      toast({
        title: 'Success',
        description: 'Indexing stopped!',
      })
      await loadData()
    } catch (err) {
      toast({
        title: 'Error',
        description:
          err instanceof Error ? err.message : 'Failed to stop indexing',
        variant: 'destructive',
      })
    }
  }


  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="flex-1 overflow-auto bg-background">
        <div className="w-full max-w-[1920px] mx-auto p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Settings2 className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold">Settings</h1>
            </div>
            {saving && (
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Saving...</span>
              </div>
            )}
          </div>

          {/* Bento Grid Layout */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
            {/* Main Content - Left Side */}
            <div className="xl:col-span-8 space-y-4">
              {/* Photo Folders Card - Compact Design */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                      <FolderOpen className="h-4 w-4 text-primary" />
                      <span>Photo Folders</span>
                    </CardTitle>
                    <Button
                      onClick={addRootFolder}
                      size="sm"
                      className="!bg-gradient-to-r !from-[rgb(var(--pink-rgb))] !to-[rgb(var(--pink-rgb))] hover:!from-[rgb(var(--pink-rgb))]/80 hover:!to-[rgb(var(--pink-rgb))]/80 !text-black !border-[rgb(var(--pink-rgb))]/50 !shadow-[var(--shadow-pink)] hover:!shadow-[var(--shadow-pink)] hover:scale-105 transition-all disabled:opacity-50 disabled:hover:scale-100"
                    >
                      <FolderPlus className="h-4 w-4 mr-1" />
                      Add
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  {rootFolders.length === 0 ? (
                    <div className="text-center py-6 space-y-3">
                      <FolderOpen className="h-10 w-10 mx-auto text-muted-foreground/50" />
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">No folders configured</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Add folders containing your photos to start indexing
                        </p>
                      </div>
                      <div className="text-xs text-muted-foreground bg-muted/50 rounded-md p-3 mx-4">
                        <p className="font-medium mb-1">Quick Start:</p>
                        <p>1. Click "Add" above to select a folder</p>
                        <p>2. Choose folders with your photos</p>
                        <p>3. Click "Save Configuration" when done</p>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      {rootFolders.slice(0, 3).map((folder, index) => (
                        <div
                          key={index}
                          className="group flex items-center justify-between py-1.5 px-2 rounded hover:bg-muted/50 transition-all"
                        >
                          <span className="font-mono text-xs truncate flex-1 text-muted-foreground">
                            {folder}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeRootFolder(index)}
                            className="h-6 w-6 p-0 !text-[var(--neon-red)] hover:!bg-gradient-to-r hover:!from-[rgb(var(--red-rgb))]/20 hover:!to-[rgb(var(--red-rgb))]/30 hover:!shadow-md hover:!shadow-[var(--shadow-red)] opacity-0 group-hover:opacity-100 !transition-all"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      ))}
                      {rootFolders.length > 3 && (
                        <>
                          <details className="cursor-pointer">
                            <summary className="text-xs text-muted-foreground hover:text-foreground transition-colors py-1">
                              Show {rootFolders.length - 3} more folders...
                            </summary>
                            <div className="space-y-1 mt-1">
                              {rootFolders.slice(3).map((folder, index) => (
                                <div
                                  key={index + 3}
                                  className="group flex items-center justify-between py-1.5 px-2 rounded hover:bg-muted/50 transition-all"
                                >
                                  <span className="font-mono text-xs truncate flex-1 text-muted-foreground">
                                    {folder}
                                  </span>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => removeRootFolder(index + 3)}
                                    className="h-6 w-6 p-0 !text-[var(--neon-red)] hover:!bg-gradient-to-r hover:!from-[rgb(var(--red-rgb))]/20 hover:!to-[rgb(var(--red-rgb))]/30 hover:!shadow-md hover:!shadow-[var(--shadow-red)] opacity-0 group-hover:opacity-100 !transition-all"
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                </div>
                              ))}
                            </div>
                          </details>
                        </>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Indexing Control Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Zap className="h-5 w-5 text-orange-600" />
                    <span>Library Updates</span>
                  </CardTitle>
                  <CardDescription>
                    Refresh your photo library
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {indexStatus && (
                    <div className="p-4 border rounded-lg bg-card">
                      <div className="flex items-center justify-between mb-3">
                        <Label>Status</Label>
                        <Badge
                          variant={
                            indexStatus.status === 'indexing'
                              ? 'default'
                              : indexStatus.status === 'error'
                                ? 'destructive'
                                : 'secondary'
                          }
                        >
                          {indexStatus.status}
                        </Badge>
                      </div>
                      {indexStatus.status === 'indexing' && (
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="text-sm font-medium capitalize">
                              Phase: {indexStatus.progress.current_phase}
                            </div>
                            {indexStatus.progress.total_files > 0 && (
                              <div className="text-sm text-muted-foreground">
                                {Math.round((indexStatus.progress.processed_files / indexStatus.progress.total_files) * 100)}%
                              </div>
                            )}
                          </div>
                          {indexStatus.progress.total_files > 0 ? (
                            <>
                              <Progress
                                value={indexStatus.progress.total_files > 0 ? (indexStatus.progress.processed_files / indexStatus.progress.total_files) * 100 : 0}
                                className="h-2"
                              />
                              <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span>
                                  {indexStatus.progress.processed_files}/{indexStatus.progress.total_files} files
                                </span>
                                {indexStatus.estimated_completion && (
                                  <span>
                                    Est. {new Date(indexStatus.estimated_completion).toLocaleTimeString()}
                                  </span>
                                )}
                              </div>
                            </>
                          ) : (
                            <div className="flex items-center space-x-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
                              <span className="text-sm text-muted-foreground">
                                Initializing {indexStatus.progress.current_phase}...
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-3">
                    <Button
                      onClick={() => startIndexing(false)}
                      disabled={indexStatus?.status === 'indexing'}
                      title={indexStatus?.status === 'indexing' ? 'Indexing in progress - please wait for it to complete' : 'Start incremental indexing for new photos'}
                      className="[background:var(--gradient-green)] text-black font-semibold shadow-md shadow-green-500/30 hover:shadow-lg hover:shadow-green-500/40 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed transition-all relative group"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Quick Update
                      {indexStatus?.status === 'indexing' && (
                        <span className="absolute -top-8 left-1/2 -translate-x-1/2 text-xs bg-black/90 text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                          Indexing in progress...
                        </span>
                      )}
                    </Button>
                    <Button
                      onClick={() => startIndexing(true)}
                      disabled={indexStatus?.status === 'indexing'}
                      title={indexStatus?.status === 'indexing' ? 'Indexing in progress - please wait for it to complete' : 'Re-index all photos from scratch'}
                      className="!bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 transition-all disabled:opacity-50 disabled:hover:scale-100"
                    >
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Full Refresh
                      {indexStatus?.status === 'indexing' && (
                        <span className="absolute -top-8 left-1/2 -translate-x-1/2 text-xs bg-black/90 text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                          Indexing in progress...
                        </span>
                      )}
                    </Button>
                  </div>

                  {indexStatus?.status === 'indexing' && (
                    <Button
                      onClick={stopIndexing}
                      variant="destructive"
                      className="w-full !bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !font-semibold !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] hover:!scale-[1.02] !border !border-[rgb(var(--red-rgb))]/30 hover:!border-[rgb(var(--red-rgb))]/50 !transition-all"
                    >
                      <Square className="h-4 w-4 mr-2" />
                      Stop Indexing
                    </Button>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Sidebar - Right Side */}
            <div className="xl:col-span-4 space-y-4">
              {/* Search Features Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">Search Features</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Smart Search Toggle */}
                  <div className="flex items-center justify-between py-2">
                    <div className="space-y-0.5">
                      <Label htmlFor="semantic-search" className="text-sm font-medium">
                        Smart Search
                      </Label>
                      <p className="text-xs text-muted-foreground">
                        Search by description
                      </p>
                    </div>
                    <Switch
                      id="semantic-search"
                      checked={semanticSearchEnabled}
                      onCheckedChange={setSemanticSearchEnabled}
                    />
                  </div>

                  {/* Text Recognition Toggle - Only show if OCR is available */}
                  {isOcrAvailable && (
                    <>
                      <div className="flex items-center justify-between py-2">
                        <div className="space-y-0.5">
                          <Label htmlFor="ocr-enabled" className="text-sm font-medium">
                            Text Recognition
                          </Label>
                          <p className="text-xs text-muted-foreground">
                            Find text in photos
                          </p>
                        </div>
                        <Switch
                          id="ocr-enabled"
                          checked={ocrEnabled}
                          onCheckedChange={setOcrEnabled}
                        />
                      </div>

                      {/* OCR Languages - Only show when enabled */}
                      {ocrEnabled && (
                        <div className="pl-4 space-y-2 border-l-2 border-primary/30">
                          <Label className="text-xs font-medium">Languages</Label>
                          {[
                            { code: 'eng', name: 'English' },
                            { code: 'tam', name: 'Tamil' },
                          ].map(({ code, name }) => (
                            <div key={code} className="flex items-center space-x-2">
                              <Checkbox
                                id={`ocr-${code}`}
                                checked={ocrLanguages.includes(code)}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    setOcrLanguages([...ocrLanguages, code])
                                  } else {
                                    setOcrLanguages(ocrLanguages.filter(l => l !== code))
                                  }
                                }}
                              />
                              <Label
                                htmlFor={`ocr-${code}`}
                                className="text-xs cursor-pointer"
                              >
                                {name}
                              </Label>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}

                  {/* Face Search Toggle */}
                  <div className="flex items-center justify-between py-2">
                    <div className="space-y-0.5">
                      <Label htmlFor="face-search" className="text-sm font-medium">
                        People Search
                      </Label>
                      <p className="text-xs text-muted-foreground">
                        Find faces in photos
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

              {/* Reset Onboarding */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">Setup Wizard</CardTitle>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => {
                      resetOnboarding()
                      toast({
                        title: 'Onboarding Reset',
                        description: 'The setup wizard will appear on next app launch.',
                      })
                    }}
                    className="w-full !bg-gradient-to-r !from-[rgb(var(--cyan-rgb))] !to-[rgb(var(--cyan-rgb))] !text-black !font-semibold !shadow-[var(--shadow-cyan)] hover:!shadow-[var(--shadow-cyan)] hover:!scale-[1.02] !transition-all"
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Run Setup Again
                  </Button>
                </CardContent>
              </Card>

            </div>
          </div>
        </div>
      </div>

      <Toaster />
    </>
  )
}
