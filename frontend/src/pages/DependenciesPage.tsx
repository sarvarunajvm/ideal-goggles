import { useState, useEffect, useCallback } from 'react'
import {
  apiService,
  DependenciesResponse,
  DependencyVerificationResponse,
  ModelVerificationDetails
} from '../services/apiClient'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/components/ui/use-toast'
import { Toaster } from '@/components/ui/toaster'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
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
  AlertTriangle,
  Info,
  Shield,
  Brain,
  Zap,
} from 'lucide-react'

export default function DependenciesPage() {
  const [dependencies, setDependencies] = useState<DependenciesResponse | null>(null)
  const [verification, setVerification] = useState<DependencyVerificationResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
  const [installing, setInstalling] = useState<string | null>(null)
  const [installProgress, setInstallProgress] = useState(0)
  const { toast } = useToast()

  const fetchDependencies = useCallback(async () => {
    try {
      setLoading(true)
      const deps = await apiService.getDependencies()
      setDependencies(deps)
    } catch (error) {
      console.error('Failed to fetch dependencies:', error)
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
          semantic_search: false,
          face_recognition: false,
          face_detection: false,
          thumbnail_generation: true,
        },
      })
    } finally {
      setLoading(false)
    }
  }, [])

  const verifyDependencies = useCallback(async () => {
    try {
      setVerifying(true)
      const result = await apiService.verifyDependencies()
      setVerification(result)

      // Show toast based on verification status
      if (result.summary.all_functional) {
        toast({
          title: 'All Systems Ready',
          description: 'All dependencies and models are properly configured',
        })
      } else if (result.summary.issues_found.length > 0) {
        const issueCount = result.summary.issues_found.length
        toast({
          title: 'Issues Found',
          description: `${issueCount} model${issueCount > 1 ? 's' : ''} have issues. Check details below.`,
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to verify dependencies:', error)
      toast({
        title: 'Verification Failed',
        description: 'Could not verify dependencies status',
        variant: 'destructive',
      })
    } finally {
      setVerifying(false)
    }
  }, [toast])

  useEffect(() => {
    fetchDependencies()
    verifyDependencies()
  }, [fetchDependencies, verifyDependencies])

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
        await verifyDependencies()
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
        await verifyDependencies()
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-400" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-400" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-400" />
      default:
        return <Info className="h-4 w-4 text-blue-400" />
    }
  }

  const getStatusColor = (allFunctional: boolean) => {
    return allFunctional
      ? 'text-green-400 border-green-400/30 bg-green-400/5'
      : 'text-red-400 border-red-400/30 bg-red-400/5'
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
          {/* Header */}
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Package className="h-6 w-6 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Dependencies</h1>
                <p className="text-xs text-muted-foreground">Manage components and verify system status</p>
              </div>
            </div>
            <div className="flex space-x-2">
              <Button
                size="sm"
                onClick={verifyDependencies}
                disabled={verifying || installing !== null}
                variant="outline"
                className="h-8"
              >
                {verifying ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <>
                    <Shield className="h-3 w-3 mr-1" />
                    Verify
                  </>
                )}
              </Button>
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
          </div>

          {/* System Status Alert */}
          {verification && (
            <Alert className={`mb-4 ${getStatusColor(verification.summary.all_functional)}`}>
              <div className="flex items-start space-x-2">
                {verification.summary.all_functional ? (
                  <CheckCircle2 className="h-4 w-4 mt-0.5" />
                ) : (
                  <XCircle className="h-4 w-4 mt-0.5" />
                )}
                <div className="flex-1">
                  <AlertTitle className="text-sm font-medium">
                    {verification.summary.all_functional ? 'System Ready' : 'Issues Detected'}
                  </AlertTitle>
                  <AlertDescription className="text-xs mt-1">
                    {verification.summary.all_functional ? (
                      'All dependencies and models are properly configured and ready to use.'
                    ) : (
                      <>
                        {verification.summary.issues_found.map((issue, idx) => (
                          <div key={idx} className="mb-1">
                            <strong>{issue.model}:</strong> {issue.error}
                          </div>
                        ))}
                      </>
                    )}
                  </AlertDescription>
                  {verification.system && (
                    <div className="mt-2 text-xs opacity-80">
                      System: {verification.system.platform} {verification.system.architecture} •
                      Python {verification.system.python_version} •
                      Memory: {verification.system.memory.available_gb}GB/{verification.system.memory.total_gb}GB available
                    </div>
                  )}
                  {verification.recommendations && verification.recommendations.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {verification.recommendations.map((rec, idx) => (
                        <p key={idx} className="text-xs opacity-80">• {rec}</p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </Alert>
          )}

          {/* Main Grid Layout */}
          <div className="grid grid-cols-12 gap-3 flex-1 min-h-0">
            {/* Core & ML Dependencies */}
            <Card className="col-span-8 overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2 text-base">
                  <Database className="h-4 w-4 text-primary" />
                  <span>Components</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-2 space-y-4">
                {/* Core Dependencies */}
                <div>
                  <h4 className="text-sm font-medium mb-2 text-primary">Core Components (Required)</h4>
                  <div className="grid grid-cols-2 gap-2">
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

                {/* ML Dependencies */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-purple-400">Machine Learning Components</h4>
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
                  <div className="grid grid-cols-2 gap-3">
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

            {/* Model Verification Status */}
            <Card className="col-span-4 overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2 text-base">
                  <Brain className="h-4 w-4 text-purple-400" />
                  <span>Model Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-2">
                {verification?.models ? (
                  <div className="space-y-2">
                    {Object.entries(verification.models).map(([modelType, model]) => (
                      <div
                        key={modelType}
                        className={`p-2 rounded border ${
                          model.functional
                            ? 'bg-green-500/5 border-green-500/30'
                            : 'bg-red-500/5 border-red-500/30'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium capitalize">{modelType}</span>
                          {model.functional ? (
                            <CheckCircle2 className="h-4 w-4 text-green-400" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-400" />
                          )}
                        </div>
                        {model.functional ? (
                          <div className="text-xs text-muted-foreground">
                            {model.details.model_name && (
                              <div>Model: {model.details.model_name}</div>
                            )}
                            {model.details.device && (
                              <div>Device: {model.details.device}</div>
                            )}
                            <div>Memory: {model.details.available_memory_gb}GB available</div>
                          </div>
                        ) : (
                          <p className="text-xs text-red-400">{model.error}</p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <Zap className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                    <p className="text-xs text-muted-foreground">
                      Click "Verify" to check model status
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Features Status */}
            <Card className="col-span-12 overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2 text-base">
                  <Zap className="h-4 w-4 text-yellow-400" />
                  <span>Available Features</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-2">
                <div className="grid grid-cols-3 lg:grid-cols-6 gap-2">
                  {Object.entries(dependencies.features).map(([feature, enabled]) => (
                    <div
                      key={feature}
                      className={`p-2 rounded text-center ${
                        enabled
                          ? 'bg-green-500/10 border border-green-500/30'
                          : 'bg-muted/50 border border-muted'
                      }`}
                    >
                      <div className="flex items-center justify-center mb-1">
                        {enabled ? (
                          <CheckCircle2 className="h-3 w-3 text-green-400" />
                        ) : (
                          <XCircle className="h-3 w-3 text-muted-foreground" />
                        )}
                      </div>
                      <p className="text-xs">
                        {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Installation Progress */}
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