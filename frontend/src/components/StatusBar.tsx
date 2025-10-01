import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Wifi,
  WifiOff,
  Loader2,
  Zap,
  CheckCircle,
  XCircle,
  Pause,
  ExternalLink,
  BookOpen,
  AlertCircle
} from 'lucide-react';
import { apiService, IndexStatus, getApiBaseUrl } from '../services/apiClient';

export default function StatusBar() {
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [healthStatus, setHealthStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  useEffect(() => {
    // Check health and index status every 5 seconds
    const checkStatus = async () => {
      try {
        const [, index] = await Promise.all([
          apiService.getHealth(),
          apiService.getIndexStatus(),
        ]);

        setHealthStatus('connected');
        setIndexStatus(index);
      } catch (error) {
        setHealthStatus('disconnected');
        setIndexStatus(null);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'indexing':
        return 'default';
      case 'error':
        return 'destructive';
      case 'idle':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'indexing':
        return Zap;
      case 'error':
        return XCircle;
      case 'idle':
        return CheckCircle;
      default:
        return Pause;
    }
  };

  const getConnectionIcon = () => {
    switch (healthStatus) {
      case 'connected':
        return Wifi;
      case 'disconnected':
        return WifiOff;
      default:
        return Loader2;
    }
  };

  const getConnectionBadgeVariant = () => {
    switch (healthStatus) {
      case 'connected':
        return 'secondary';
      case 'disconnected':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getConnectionText = () => {
    switch (healthStatus) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Checking...';
    }
  };

  const getProgressPercentage = () => {
    if (!indexStatus || indexStatus.status !== 'indexing' || indexStatus.progress.total_files === 0) {
      return 0;
    }
    return (indexStatus.progress.processed_files / indexStatus.progress.total_files) * 100;
  };

  return (
    <footer className="bg-card border-t border-border px-4 py-2 shrink-0">
      <div className="flex items-center justify-between text-xs sm:text-sm">
        {/* Connection Status */}
        <div className="flex items-center space-x-3">
          <Badge
            variant={getConnectionBadgeVariant()}
            className={`transition-all duration-300 ${
              healthStatus === 'checking' ? 'animate-pulse' : ''
            }`}
            data-testid="connection-badge"
          >
            {(() => {
              const IconComponent = getConnectionIcon();
              return (
                <>
                  <IconComponent className={`w-3 h-3 mr-1.5 ${
                    healthStatus === 'checking' ? 'animate-spin' : ''
                  }`} />
                  {getConnectionText()}
                </>
              );
            })()}
          </Badge>
        </div>

        {/* Index Status */}
        <div className="flex items-center space-x-3">
          {indexStatus && (
            <>
              <Badge
                variant={getStatusBadgeVariant(indexStatus.status)}
                className="transition-all duration-300"
              >
                {(() => {
                  const IconComponent = getStatusIcon(indexStatus.status);
                  return (
                    <>
                      <IconComponent className={`w-3 h-3 mr-1.5 ${
                        indexStatus.status === 'indexing' ? 'animate-pulse' : ''
                      }`} />
                      {indexStatus.status.charAt(0).toUpperCase() + indexStatus.status.slice(1)}
                    </>
                  );
                })()}
              </Badge>

              {indexStatus.status === 'indexing' && (
                <div className="hidden sm:flex items-center space-x-2">
                  <span className="text-muted-foreground text-xs">
                    {indexStatus.progress.current_phase}
                  </span>
                  {indexStatus.progress.total_files > 0 && (
                    <>
                      <div className="w-16">
                        <Progress
                          value={getProgressPercentage()}
                          className="h-1.5"
                        />
                      </div>
                      <span className="text-muted-foreground text-xs">
                        {indexStatus.progress.processed_files}/{indexStatus.progress.total_files}
                      </span>
                    </>
                  )}
                </div>
              )}

              {indexStatus.errors.length > 0 && (
                <Badge variant="destructive" className="animate-pulse">
                  <AlertCircle className="w-3 h-3 mr-1.5" />
                  {indexStatus.errors.length} error{indexStatus.errors.length !== 1 ? 's' : ''}
                </Badge>
              )}
            </>
          )}
        </div>

        {/* Quick Actions */}
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open(`${getApiBaseUrl()}/docs`, '_blank')}
            className="h-7 px-2 text-xs hover:scale-105 transition-all duration-200"
            title="Open API Documentation"
          >
            <BookOpen className="w-3 h-3 mr-1.5" />
            <span className="hidden sm:inline">API Docs</span>
            <ExternalLink className="w-2.5 h-2.5 ml-1" />
          </Button>
        </div>
      </div>

      {/* Mobile-friendly indexing progress */}
      {indexStatus && indexStatus.status === 'indexing' && (
        <div className="sm:hidden mt-2 pb-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>{indexStatus.progress.current_phase}</span>
            {indexStatus.progress.total_files > 0 && (
              <span>
                {indexStatus.progress.processed_files}/{indexStatus.progress.total_files}
              </span>
            )}
          </div>
          {indexStatus.progress.total_files > 0 && (
            <Progress
              value={getProgressPercentage()}
              className="h-1"
            />
          )}
        </div>
      )}
    </footer>
  );
}
