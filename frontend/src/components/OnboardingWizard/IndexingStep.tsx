import { useEffect, useState } from 'react';
import { useOnboardingStore } from '../../stores/onboardingStore';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';

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

  useEffect(() => {
    startIndexing();
    const interval = setInterval(pollIndexingStatus, 500);
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

  const startIndexing = async () => {
    try {
      setIndexingStarted(true);

      // First, configure the roots
      await axios.post(`${API_BASE}/config/roots`, {
        roots: selectedFolders,
      });

      // Then start indexing
      await axios.post(`${API_BASE}/index/start`, {
        full: true,
      });
    } catch (err: any) {
      if (err.response?.status !== 409) {
        // 409 means already indexing, which is fine
        setError(err.message || 'Failed to start indexing');
      }
    }
  };

  const pollIndexingStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/index/status`);
      const data: IndexingStatus = response.data;
      console.log('Indexing status:', data); // Debug log
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
    <div className="space-y-6">
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
          <div className="flex items-center space-x-3 text-destructive">
            <AlertCircle className="h-6 w-6" />
            <div>
              <p className="font-medium">Error occurred</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        ) : isComplete ? (
          <div className="flex items-center space-x-3 text-green-400">
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
                  {status ? getPhaseLabel(status.progress.current_phase) : 'Starting...'}
                </p>
                {status && status.progress.processed_files > 0 && (
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

            {/* Progress bar */}
            <div className="space-y-2">
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted/50 border border-border/50">
                <div
                  className="h-full bg-gradient-to-r from-primary to-yellow-300 transition-all duration-500 shadow-sm"
                  style={{
                    width: status && status.progress && status.progress.total_files > 0
                      ? `${(status.progress.processed_files / status.progress.total_files) * 100}%`
                      : status?.status === 'indexing' ? '5%' : '0%',
                  }}
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground/90 text-center font-medium">
                  {status?.progress?.processed_files || 0} / {status?.progress?.total_files || '?'}{' '}
                  photos {status?.progress && status?.progress.total_files > 0 &&
                    `(${Math.round((status.progress.processed_files / status.progress.total_files) * 100)}%)`
                  }
                </p>
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
                {status?.progress.processed_files ? `${status.progress.processed_files} photos ready to search.` : ''} Continue while we finish in the background.
              </p>
            </div>
            <button
              onClick={handleContinueInBackground}
              className="rounded-lg px-6 py-2 font-semibold [background:var(--gradient-green)] text-black shadow-md shadow-green-500/30 hover:shadow-lg hover:shadow-green-500/40 hover:scale-[1.02] transition-all"
            >
              Skip & Start
            </button>
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
        <button
          onClick={prevStep}
          disabled={status?.status === 'indexing' || isComplete}
          className="rounded-lg px-6 py-2 font-medium [background:var(--gradient-red)] text-white disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-red-500/30 hover:shadow-lg hover:shadow-red-500/40 hover:scale-[1.02] transition-all"
        >
          Back
        </button>
        <button
          onClick={handleNext}
          disabled={!isComplete}
          className="rounded-lg px-6 py-2 font-semibold [background:var(--gradient-gold)] text-black disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-primary/30 hover:shadow-lg hover:shadow-primary/40 hover:scale-[1.02] transition-all"
        >
          {isComplete ? 'Continue' : 'Waiting...'}
        </button>
      </div>
    </div>
  );
}
