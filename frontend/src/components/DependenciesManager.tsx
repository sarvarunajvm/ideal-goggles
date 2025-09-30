import { useState, useEffect, useCallback } from 'react';
import { apiService, DependenciesResponse, DependencyStatus } from '../services/apiClient';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import {
  CheckCircle2,
  XCircle,
  Download,
  Loader2,
  Info,
  Package,
  Cpu,
  Eye,
  Type,
  AlertCircle,
  RefreshCw
} from 'lucide-react';

interface DependencyCardProps {
  dependency: DependencyStatus;
  onInstall?: () => void;
  installing?: boolean;
}

function DependencyCard({ dependency, onInstall, installing }: DependencyCardProps) {
  const getIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case 'tesseract':
        return <Type className="h-5 w-5" />;
      case 'pytorch':
      case 'clip':
        return <Cpu className="h-5 w-5" />;
      case 'insightface':
      case 'opencv':
        return <Eye className="h-5 w-5" />;
      default:
        return <Package className="h-5 w-5" />;
    }
  };

  return (
    <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
      <div className="flex items-start space-x-3">
        <div className="mt-0.5">{getIcon(dependency.name)}</div>
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <h4 className="font-medium">{dependency.name}</h4>
            {dependency.version && (
              <span className="text-xs text-muted-foreground">v{dependency.version}</span>
            )}
            {dependency.required && (
              <Badge variant="secondary" className="text-xs">Required</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-1">{dependency.description}</p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        {dependency.installed ? (
          <Badge variant="success" className="flex items-center space-x-1">
            <CheckCircle2 className="h-3 w-3" />
            <span>Installed</span>
          </Badge>
        ) : (
          <>
            {!dependency.required && onInstall && (
              <Button
                size="sm"
                variant="outline"
                onClick={onInstall}
                disabled={installing}
              >
                {installing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-1" />
                    Install
                  </>
                )}
              </Button>
            )}
            <Badge variant="outline" className="flex items-center space-x-1">
              <XCircle className="h-3 w-3" />
              <span>Not Installed</span>
            </Badge>
          </>
        )}
      </div>
    </div>
  );
}

export default function DependenciesManager() {
  const [dependencies, setDependencies] = useState<DependenciesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState<string | null>(null);
  const [installProgress, setInstallProgress] = useState(0);
  const { toast } = useToast();

  const fetchDependencies = useCallback(async () => {
    try {
      setLoading(true);
      const deps = await apiService.getDependencies();
      setDependencies(deps);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch dependencies status",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchDependencies();
  }, [fetchDependencies]);

  const handleInstall = async (component: string) => {
    setInstalling(component);
    setInstallProgress(0);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setInstallProgress(prev => Math.min(prev + 10, 90));
      }, 1000);

      const result = await apiService.installDependencies([component.toLowerCase()]);

      clearInterval(progressInterval);
      setInstallProgress(100);

      if (result.status === 'success') {
        toast({
          title: "Success",
          description: `${component} installed successfully`,
        });
        // Refresh dependencies
        await fetchDependencies();
      } else {
        toast({
          title: "Warning",
          description: `${component} installation completed with warnings`,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to install ${component}`,
        variant: "destructive"
      });
    } finally {
      setInstalling(null);
      setInstallProgress(0);
    }
  };

  const handleInstallAll = async () => {
    setInstalling('all');
    setInstallProgress(0);

    try {
      const progressInterval = setInterval(() => {
        setInstallProgress(prev => Math.min(prev + 5, 90));
      }, 2000);

      const result = await apiService.installDependencies(['all']);

      clearInterval(progressInterval);
      setInstallProgress(100);

      if (result.status === 'success') {
        toast({
          title: "Success",
          description: "All ML dependencies installed successfully",
        });
        await fetchDependencies();
      } else {
        toast({
          title: "Warning",
          description: "Some dependencies may have failed to install",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to install dependencies",
        variant: "destructive"
      });
    } finally {
      setInstalling(null);
      setInstallProgress(0);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!dependencies) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          Failed to load dependencies information. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  const allMLInstalled = dependencies.ml.every(d => d.installed);

  return (
    <div className="space-y-6">
      {/* Features Status */}
      <Card>
        <CardHeader>
          <CardTitle>Feature Availability</CardTitle>
          <CardDescription>
            Features available based on installed dependencies
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(dependencies.features).map(([feature, available]) => (
              <div
                key={feature}
                className="flex items-center space-x-2 p-2 rounded-lg border"
              >
                {available ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                )}
                <span className={`text-sm ${available ? '' : 'text-muted-foreground'}`}>
                  {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Core Dependencies */}
      <Card>
        <CardHeader>
          <CardTitle>Core Dependencies</CardTitle>
          <CardDescription>
            Required dependencies for basic functionality
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {dependencies.core.map(dep => (
            <DependencyCard key={dep.name} dependency={dep} />
          ))}
        </CardContent>
      </Card>

      {/* ML Dependencies */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>ML Dependencies</CardTitle>
              <CardDescription className="mt-1">
                Optional dependencies for advanced features
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchDependencies}
                disabled={installing !== null}
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Refresh
              </Button>
              {!allMLInstalled && (
                <Button
                  size="sm"
                  onClick={handleInstallAll}
                  disabled={installing !== null}
                >
                  {installing === 'all' ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1" />
                  ) : (
                    <Download className="h-4 w-4 mr-1" />
                  )}
                  Install All
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {dependencies.ml.map(dep => (
            <DependencyCard
              key={dep.name}
              dependency={dep}
              onInstall={() => handleInstall(dep.name)}
              installing={installing === dep.name}
            />
          ))}
        </CardContent>
      </Card>

      {/* Installation Progress */}
      {installing && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Installing {installing}...</span>
                <span>{installProgress}%</span>
              </div>
              <Progress value={installProgress} />
              <p className="text-xs text-muted-foreground">
                This may take several minutes depending on your internet connection and system.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Information Alert */}
      {!allMLInstalled && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Optional Dependencies</AlertTitle>
          <AlertDescription>
            ML dependencies enable advanced features like OCR text extraction, semantic search,
            and face recognition. These features are optional and the app works without them.
            Installation may require several GB of disk space.
          </AlertDescription>
        </Alert>
      )}

      {allMLInstalled && (
        <Alert className="border-green-200 bg-green-50 dark:bg-green-950/20">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertTitle>All Set!</AlertTitle>
          <AlertDescription>
            All ML dependencies are installed. You can now use advanced features like
            semantic search, OCR text extraction, and face recognition.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}