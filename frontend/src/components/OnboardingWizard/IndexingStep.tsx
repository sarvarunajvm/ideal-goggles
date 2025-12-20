import { useEffect, useState } from 'react';
import { useOnboardingStore } from '../../stores/onboardingStore';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

const API_BASE = 'http://localhost:5555';

interface IndexingStatus {
  status: string; // 'idle', 'indexing', 'completed', 'error'
  progress: {
    total_files: number;
    processed_files: number;
    current_phase: string;
  };
  errors: string[];
  started_at: string | null;
  estimated_completion: string | null;
}

const funFacts = [
  "💡 You'll be able to search for photos by describing what's in them - like 'dog playing in snow' or 'sunset at the beach'",
  "🔍 No more endless scrolling! Find that one photo from years ago in seconds",
  "🎯 Search by text that appears in photos - perfect for finding screenshots, documents, or signs",
  "👥 Once set up, you can find all photos of specific people instantly",
  "🏷️ Your photos are automatically tagged with helpful labels like 'outdoor', 'food', or 'celebration'",
  "🔒 Everything stays on your computer - your photos are never uploaded anywhere",
  "⚡ After this one-time setup, searching will be instant every time",
  "📅 You can search by date ranges to find photos from specific events or trips",
];

export function IndexingStep() {
  const { selectedFolders, setIndexingStarted, nextStep, prevStep, setCompleted } =
    useOnboardingStore();
  const navigate = useNavigate();
  const [status, setStatus] = useState<IndexingStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [currentFactIndex, setCurrentFactIndex] = useState(0);
  // Track elapsed onboarding time (reserved for future UX tweaks)
  const [, setElapsedTime] = useState<number>(0);
  const [showBackgroundOption, setShowBackgroundOption] = useState(false);
  const [retryAttempts, setRetryAttempts] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  useEffect(() => {
    startIndexing();
    const interval = setInterval(pollIndexingStatus, 2000); // Reduced from 500ms to 2s for better performance
    return () => clearInterval(interval);
  }, []);

  // Rotate fun facts every 5 seconds during indexing
  useEffect(() => {
    if (!isComplete && status?.status === 'indexing') {
      const factInterval = setInterval(() => {
        setCurrentFactIndex((prev) => (prev + 1) % funFacts.length);
      }, 5000);
      return () => clearInterval(factInterval);
    }
  }, [isComplete, status?.status]);

  // Track elapsed time and show background option after 5 seconds
  useEffect(() => {
    if (status?.status === 'indexing' && !isComplete) {
      const timeInterval = setInterval(() => {
        setElapsedTime((prev) => {
          const newTime = prev + 1;
          if (newTime >= 5 && !showBackgroundOption) {
            setShowBackgroundOption(true);
          }
          return newTime;
        });
      }, 1000);
      return () => clearInterval(timeInterval);
    }
  }, [status?.status, isComplete, showBackgroundOption]);

  const startIndexing = async (isRetry = false) => {
    try {
      if (isRetry) {
        setIsRetrying(true);
        setError(null);
      } else {
        setIndexingStarted(true);
      }

      // First, configure the roots
      await axios.post(`${API_BASE}/config/roots`, {
        roots: selectedFolders,
      });

      // Then start indexing
      await axios.post(`${API_BASE}/index/start`, {
        full: true,
      });

      if (isRetry) {
        setIsRetrying(false);
      }
    } catch (err: any) {
      if (err.response?.status !== 409) {
        // 409 means already indexing, which is fine
        setError(err.message || 'Failed to start indexing');
        if (isRetry) {
          setIsRetrying(false);
        }
      }
    }
  };

  const handleRetry = async () => {
    const newAttemptCount = retryAttempts + 1;
    setRetryAttempts(newAttemptCount);
    await startIndexing(true);
  };

  const pollIndexingStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/index/status`);
      const data: IndexingStatus = response.data;
      setStatus(data);

      // Check if indexing is complete
      if (data.status === 'completed' || (data.status === 'idle' && data.progress.processed_files > 0)) {
        setIsComplete(true);
      }

      // Check for errors
      if (data.errors && data.errors.length > 0) {
        setError(data.errors[0]);
      }
    } catch (err) {
      console.error('Failed to poll indexing status:', err);
    }
  };

  const getPhaseLabel = (phase: string) => {
    const phaseLabels: Record<string, string> = {
      discovery: 'Finding your photos',
      scanning: 'Looking through your photos',
      thumbnails: 'Creating preview images',
      metadata: 'Reading photo information',
      ocr: 'Reading text in photos',
      embeddings: 'Making photos searchable',
      faces: 'Finding faces in photos',
      tagging: 'Adding helpful labels',
      completed: 'All done!',
      complete: 'All done!',
    };
    return phaseLabels[phase] || phase || 'Working on it...';
  };

  const handleNext = () => {
    if (isComplete) {
      nextStep();
    }
  };

  const handleContinueInBackground = () => {
    // Mark onboarding as complete and let indexing continue in background
    setCompleted();
    // Navigate to home page (which shows the search page)
    navigate('/');
  };

  return (
    <div className="space-y-6" data-testid="indexing-step">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-foreground">
          Setting Up Your Photo Library
        </h2>
        <p className="mt-2 text-muted-foreground">
          Sit back and relax - we're making your photos searchable!
        </p>
      </div>

      {/* Status display */}
      <div className="rounded-lg border border-border/50 bg-background/50 p-6">
        {error ? (
          <div className="space-y-4" data-testid="indexing-error">
            <div className="flex items-center space-x-3 text-destructive">
              <AlertCircle className="h-6 w-6" />
              <div className="flex-1">
                <p className="font-medium">Setup failed</p>
                <p className="text-sm">{error}</p>
                {retryAttempts > 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Retry attempt {retryAttempts}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                onClick={handleRetry}
                disabled={isRetrying || retryAttempts >= 3}
                size="sm"
                className="!bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !border-[rgb(var(--red-rgb))]/50 !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] hover:scale-105 !font-semibold transition-all disabled:opacity-50 disabled:hover:scale-100"
                data-testid="retry-indexing-btn"
              >
                {isRetrying ? (
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Retrying...</span>
                  </div>
                ) : retryAttempts >= 3 ? (
                  'Max retries reached'
                ) : (
                  `Try again${retryAttempts > 0 ? ` (${3 - retryAttempts} left)` : ''}`
                )}
              </Button>
              {retryAttempts >= 3 && (
                <p className="text-xs text-muted-foreground">
                  Please check your folder permissions and try going back to select different folders.
                </p>
              )}
            </div>
          </div>
        ) : isComplete ? (
          <div className="flex items-center space-x-3 text-green-400" data-testid="indexing-complete">
            <CheckCircle2 className="h-6 w-6" />
            <div>
              <p className="font-medium">All done!</p>
              <p className="text-sm text-muted-foreground">
                Found {status?.progress.processed_files || 0} photos
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <div className="flex-1">
                <p className="font-medium text-foreground">
                  {status?.progress ? getPhaseLabel(status.progress.current_phase) : 'Starting...'}
                </p>
                {status?.progress && status.progress.processed_files > 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {status.progress.processed_files < 100
                      ? "Great start! Your photos are being processed..."
                      : status.progress.processed_files < 500
                      ? "Making good progress! This will be worth it..."
                      : status.progress.processed_files < 1000
                      ? "Halfway there! Your search will be amazing..."
                      : "Almost done! Just a bit more..."}
                  </p>
                )}
              </div>
            </div>

            {/* Enhanced Progress bar with phase indicator */}
            <div className="space-y-3" data-testid="indexing-progress">
              {/* Current phase badge */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-primary rounded-full animate-pulse" />
                  <span className="text-sm font-medium text-primary">
                    {status?.progress ? getPhaseLabel(status.progress.current_phase) : 'Starting...'}
                  </span>
                </div>
                {status?.progress && status?.progress.total_files > 0 && (
                  <span className="text-sm font-mono text-muted-foreground">
                    {Math.round((status.progress.processed_files / status.progress.total_files) * 100)}%
                  </span>
                )}
              </div>

              {/* Progress bar */}
              <div className="h-4 w-full overflow-hidden rounded-full bg-muted/50 border border-border/50 shadow-inner" data-testid="progress-bar">
                {status?.progress?.total_files === 0 ? (
                  // Indeterminate progress bar for discovery phase
                  <div className="h-full bg-gradient-to-r from-primary via-yellow-300 to-primary animate-pulse">
                    <div className="h-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                  </div>
                ) : (
                  // Determinate progress bar when we know the total
                  <div
                    className="h-full bg-gradient-to-r from-primary to-yellow-300 transition-all duration-500 shadow-sm relative overflow-hidden"
                    style={{
                      width: status && status.progress && status.progress.total_files > 0
                        ? `${(status.progress.processed_files / status.progress.total_files) * 100}%`
                        : '0%',
                    }}
                  >
                    {/* Animated shine effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                  </div>
                )}
              </div>
              {/* File count and detailed progress */}
              <div className="space-y-2">
                <p className="text-sm text-foreground/90 text-center font-medium">
                  {status?.progress?.total_files === 0 ? (
                    <>Discovering photos in your folders...</>
                  ) : (
                    <>
                      {status?.progress?.processed_files || 0} / {status?.progress?.total_files || '?'}{' '}
                      photos processed
                    </>
                  )}
                </p>

                {/* Phase progress breakdown - only show when we have status */}
                {status?.progress && status.progress.total_files > 0 && (
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="text-center">
                      <div className="h-1 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-400 transition-all duration-300"
                          style={{ width: status.progress.current_phase === 'discovery' || status.progress.current_phase === 'completed' ? '100%' : '0%' }}
                        />
                      </div>
                      <span className="text-muted-foreground">Discovery</span>
                    </div>
                    <div className="text-center">
                      <div className="h-1 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-400 transition-all duration-300"
                          style={{
                            width: ['metadata', 'thumbnails', 'embeddings', 'faces', 'completed'].includes(status.progress.current_phase)
                              ? '100%'
                              : ['scanning'].includes(status.progress.current_phase)
                                ? '50%'
                                : '0%'
                          }}
                        />
                      </div>
                      <span className="text-muted-foreground">Processing</span>
                    </div>
                    <div className="text-center">
                      <div className="h-1 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-purple-400 transition-all duration-300"
                          style={{ width: ['embeddings', 'faces', 'completed'].includes(status.progress.current_phase) ? '100%' : '0%' }}
                        />
                      </div>
                      <span className="text-muted-foreground">AI Features</span>
                    </div>
                  </div>
                )}
                {status?.progress && status?.progress.total_files > 0 && status?.progress.processed_files > 0 && (
                  <p className="text-xs text-muted-foreground text-center">
                    {(() => {
                      const photosLeft = (status?.progress?.total_files || 0) - (status?.progress?.processed_files || 0);
                      const photosPerSecond = status.progress.processed_files / 30; // Rough estimate
                      const secondsLeft = Math.ceil(photosLeft / photosPerSecond);
                      const minutesLeft = Math.ceil(secondsLeft / 60);

                      if (minutesLeft <= 1) return "Almost there! Less than a minute to go...";
                      if (minutesLeft <= 5) return `About ${minutesLeft} minutes remaining - hang tight!`;
                      if (minutesLeft <= 15) return `About ${minutesLeft} minutes to go - perfect time for a coffee break ☕`;
                      return `This might take ${minutesLeft} minutes - feel free to minimize and come back`;
                    })()}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Background option after 5 seconds */}
      {showBackgroundOption && !isComplete && (
        <div className="rounded-lg bg-gradient-to-r from-green-500/20 to-green-500/30 border-2 border-green-500/50 p-4 animate-pulse-slow">
          <div className="flex items-center space-x-3">
            <Sparkles className="h-6 w-6 text-green-400 flex-shrink-0 animate-bounce" />
            <div className="flex-1">
              <p className="text-sm font-bold text-green-400">Skip the wait!</p>
              <p className="text-xs text-foreground/90">
                {status?.progress?.processed_files ? `${status.progress.processed_files} photos ready to search.` : ''} Continue while we finish in the background.
              </p>
            </div>
            <Button
              onClick={handleContinueInBackground}
              className="!bg-gradient-to-r !from-[rgb(var(--green-rgb))] !to-[rgb(var(--green-rgb))] hover:!from-[rgb(var(--green-rgb))]/80 hover:!to-[rgb(var(--green-rgb))]/80 !text-black !border-[rgb(var(--green-rgb))]/50 !shadow-[var(--shadow-green)] hover:!shadow-[var(--shadow-green)] hover:scale-105 !font-semibold transition-all"
            >
              Skip & Start
            </Button>
          </div>
        </div>
      )}

      {/* Single info box with rotating facts */}
      {!isComplete && (
        <div className="rounded-lg bg-gradient-to-r from-primary/10 to-primary/20 border border-primary/30 p-3">
          <div className="flex items-center space-x-3">
            <Sparkles className="h-5 w-5 text-primary flex-shrink-0" />
            <p className="text-sm text-foreground/90">
              {funFacts[currentFactIndex]}
            </p>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4">
        <Button
          onClick={prevStep}
          disabled={(status?.status === 'indexing' && !error) || isComplete}
          className="!bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !border-[rgb(var(--red-rgb))]/50 !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] hover:scale-105 !font-semibold transition-all disabled:opacity-50 disabled:hover:scale-100"
        >
          Back
        </Button>
        <Button
          onClick={handleNext}
          disabled={!isComplete}
          className="!bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 !font-semibold transition-all disabled:opacity-50 disabled:hover:scale-100"
          data-testid="continue-after-index-btn"
        >
          {isComplete ? 'Continue' : 'Waiting...'}
        </Button>
      </div>
    </div>
  );
}
