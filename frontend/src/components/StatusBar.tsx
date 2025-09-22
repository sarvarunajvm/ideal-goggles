import { useState, useEffect } from 'react';
import { apiService, IndexStatus } from '../services/apiClient';

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'indexing':
        return 'text-blue-600';
      case 'error':
        return 'text-red-600';
      case 'idle':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'indexing':
        return '⚡';
      case 'error':
        return '❌';
      case 'idle':
        return '✅';
      default:
        return '⏸️';
    }
  };

  return (
    <div className="bg-gray-100 border-t border-gray-200 px-6 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between text-sm">
        {/* Connection Status */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              healthStatus === 'connected' ? 'bg-green-500' :
              healthStatus === 'disconnected' ? 'bg-red-500' : 'bg-yellow-500'
            }`}></div>
            <span className="text-gray-600">
              {healthStatus === 'connected' ? 'Connected to API' :
               healthStatus === 'disconnected' ? 'Disconnected from API' : 'Checking connection...'}
            </span>
          </div>
        </div>

        {/* Index Status */}
        {indexStatus && (
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span>{getStatusIcon(indexStatus.status)}</span>
              <span className={getStatusColor(indexStatus.status)}>
                Indexing: {indexStatus.status}
              </span>
            </div>

            {indexStatus.status === 'indexing' && (
              <div className="flex items-center space-x-2">
                <span className="text-gray-600">
                  Phase: {indexStatus.progress.current_phase}
                </span>
                {indexStatus.progress.total_files > 0 && (
                  <span className="text-gray-600">
                    ({indexStatus.progress.processed_files}/{indexStatus.progress.total_files})
                  </span>
                )}
              </div>
            )}

            {indexStatus.errors.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-red-600">
                  {indexStatus.errors.length} error{indexStatus.errors.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => window.open('http://localhost:8000/docs', '_blank')}
            className="text-blue-600 hover:text-blue-800 transition-colors"
            title="Open API Documentation"
          >
            📚 API Docs
          </button>
        </div>
      </div>
    </div>
  );
}