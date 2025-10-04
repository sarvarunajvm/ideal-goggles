import { useState, useEffect, useCallback } from 'react'
import { apiService, DependenciesResponse, DependencyStatus } from '../services/apiClient'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/components/ui/use-toast'
import { Toaster } from '@/components/ui/toaster'
import {
  Package,
  CheckCircle2,
  XCircle,
  Download,
  Loader2,
  Cpu,
  Type,
  RefreshCw,
  Database,
  Image,
  Search,
  Users,
} from 'lucide-react'

export default function DependenciesPage() {
  const [dependencies, setDependencies] = useState<DependenciesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [installing, setInstalling] = useState<string | null>(null)
  const [installProgress, setInstallProgress] = useState(0)
  const { toast } = useToast()

  const fetchDependencies = useCallback(async () => {
    try {
      setLoading(true)
      const deps = await apiService.getDependencies()
      setDependencies(deps)
    } catch (error) {
      // Fallback for when ML dependencies aren't available
      setDependencies({
        core: [
          {
            name: 'SQLite',
            installed: true,
            required: true,
            version: '3.0+',
            description: 'Database for storing photo metadata',
          },
          {
            name: 'Pillow',
            installed: true,
            required: true,
            version: '10.0+',
            description: 'Image processing library',
          },
        ],
        ml: [
          {
            name: 'Tesseract',
            installed: false,
            required: false,
            version: null,
            description: 'OCR text extraction from images',
          },
          {
            name: 'PyTorch',
            installed: false,
            required: false,
            version: null,
            description: 'Deep learning framework for ML models',
          },
          {
            name: 'CLIP',
            installed: false,
            required: false,
            version: null,
            description: 'Semantic search with natural language',
          },
          {
            name: 'InsightFace',
            installed: false,
            required: false,
            version: null,
            description: 'Face detection and recognition',
          },
        ],
        features: {
          basic_search: true,
          text_extraction: false,
          semantic_search: false,
          face_recognition: false,
          image_similarity: false,
          face_detection: false,
          thumbnail_generation: true,
        },
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDependencies()
  }, [fetchDependencies])

  const handleInstall = async (component: string) => {
    setInstalling(component)
    setInstallProgress(0)

    try {
      const progressInterval = setInterval(() => {
        setInstallProgress(prev => Math.min(prev + 10, 90))
      }, 1000)

      const result = await apiService.installDependencies([component.toLowerCase()])

      clearInterval(progressInterval)
      setInstallProgress(100)

      if (result.status === 'success') {
        toast({
          title: 'Success',
          description: `${component} installed successfully`,
        })
        await fetchDependencies()
      } else {
        toast({
          title: 'Warning',
          description: `Installation completed with warnings`,
          variant: 'destructive',
        })
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to install ${component}`,
        variant: 'destructive',
      })
    } finally {
      setInstalling(null)
      setInstallProgress(0)
    }
  }

  const handleInstallAll = async () => {
    setInstalling('all')
    setInstallProgress(0)

    try {
      const progressInterval = setInterval(() => {
        setInstallProgress(prev => Math.min(prev + 5, 90))
      }, 2000)

      const result = await apiService.installDependencies(['all'])

      clearInterval(progressInterval)
      setInstallProgress(100)

      if (result.status === 'success') {
        toast({
          title: 'Success',
          description: 'All ML dependencies installed successfully',
        })
        await fetchDependencies()
      } else {
        toast({
          title: 'Warning',
          description: 'Some dependencies may have failed to install',
          variant: 'destructive',
        })
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to install dependencies',
        variant: 'destructive',
      })
    } finally {
      setInstalling(null)
      setInstallProgress(0)
    }
  }

  const getIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case 'tesseract':
        return <Type className="h-5 w-5" />
      case 'pytorch':
        return <Cpu className="h-5 w-5" />
      case 'clip':
        return <Search className="h-5 w-5" />
      case 'insightface':
        return <Users className="h-5 w-5" />
      case 'sqlite':
        return <Database className="h-5 w-5" />
      case 'pillow':
        return <Image className="h-5 w-5" />
      default:
        return <Package className="h-5 w-5" />
    }
  }


  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading dependencies...</p>
        </div>
      </div>
    )
  }

  if (!dependencies) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <XCircle className="h-12 w-12 mx-auto text-destructive" />
          <p className="text-muted-foreground">Failed to load dependencies</p>
        </div>
      </div>
    )
  }

  const allMLInstalled = dependencies.ml.length > 0 && dependencies.ml.every(d => d.installed)

  return (
    <>
      <div className="flex-1 bg-background overflow-hidden">
        <div className="w-full max-w-[1920px] mx-auto p-4 h-full flex flex-col">
          {/* Compact Header */}
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Package className="h-6 w-6 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Dependencies</h1>
                <p className="text-xs text-muted-foreground">Manage components and features</p>
              </div>
            </div>
            <Button
              size="sm"
              onClick={fetchDependencies}
              disabled={installing !== null}
              className="h-8 bg-gradient-to-r from-cyan-400 to-teal-400 text-black font-semibold shadow-md shadow-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/40 hover:scale-[1.02] transition-all"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Refresh
            </Button>
          </div>

          {/* Compact Bento Grid Layout */}
          <div className="grid grid-cols-12 gap-3 flex-1 min-h-0">
            {/* Core & ML Dependencies - Full Width */}
            <Card className="col-span-12 overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2 text-base">
                  <Database className="h-4 w-4 text-primary" />
                  <span>Components</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-2">
                {/* Core Dependencies - Compact */}
                <div className="mb-3">
                  <h4 className="text-sm font-medium mb-2 text-primary">Core Components (Required)</h4>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                    {dependencies.core.map(dep => (
                      <div
                        key={dep.name}
                        className="flex items-center space-x-2 p-3 rounded bg-primary/5 border border-primary/20"
                      >
                        {getIcon(dep.name)}
                        <div className="flex-1">
                          <p className="text-sm font-medium">{dep.name}</p>
                          <p className="text-xs text-muted-foreground">{dep.version}</p>
                        </div>
                        <CheckCircle2 className="h-4 w-4 text-green-400" />
                      </div>
                    ))}
                  </div>
                </div>

                {/* ML Dependencies - Expanded Grid */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-purple-400">Machine Learning Components (Optional)</h4>
                    {!allMLInstalled && dependencies.ml.length > 0 && (
                      <Button
                        size="sm"
                        onClick={handleInstallAll}
                        disabled={installing !== null}
                        className="h-8 px-3 text-sm bg-gradient-to-r from-violet-500 to-purple-500 text-white font-semibold shadow-md shadow-purple-500/30 hover:shadow-lg hover:shadow-purple-500/40 hover:scale-[1.02] transition-all"
                      >
                        {installing === 'all' ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <>
                            <Download className="h-4 w-4 mr-1" />
                            Install All ML
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {dependencies.ml.map(dep => (
                      <div
                        key={dep.name}
                        className={`p-3 rounded-lg border transition-all ${
                          dep.installed
                            ? 'bg-green-500/5 border-green-500/30'
                            : 'bg-muted/50 border-purple-500/30 hover:border-purple-500/50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <div className="p-1.5 rounded bg-gradient-to-br from-violet-500/20 to-purple-500/20">
                              {getIcon(dep.name)}
                            </div>
                            <p className="text-sm font-medium">{dep.name}</p>
                          </div>
                          {dep.installed ? (
                            <CheckCircle2 className="h-4 w-4 text-green-400" />
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              Not Installed
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">{dep.description}</p>
                        {!dep.installed && (
                          <Button
                            size="sm"
                            onClick={() => handleInstall(dep.name)}
                            disabled={installing !== null}
                            className="w-full h-8 text-xs bg-gradient-to-r from-violet-500 to-purple-500 text-white font-semibold shadow-md shadow-purple-500/30 hover:shadow-lg hover:shadow-purple-500/40 hover:scale-[1.02] transition-all"
                          >
                            {installing === dep.name ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <>
                                <Download className="h-3 w-3 mr-1" />
                                Install
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>


            {/* Installation Progress - Compact */}
            {installing && (
              <Card className="col-span-12 border-primary/30 bg-primary/5">
                <CardContent className="py-3">
                  <div className="flex items-center space-x-3">
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium">Installing {installing}...</span>
                        <span className="text-muted-foreground">{installProgress}%</span>
                      </div>
                      <Progress value={installProgress} className="h-1" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      <Toaster />
    </>
  )
}