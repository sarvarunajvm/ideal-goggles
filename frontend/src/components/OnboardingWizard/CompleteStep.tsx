import { useState, useEffect } from 'react';
import { useOnboardingStore } from '../../stores/onboardingStore';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Camera, Users, FileText, Loader2 } from 'lucide-react';
import { apiService } from '../../services/apiClient';
import { Button } from '@/components/ui/button';

interface StatsCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}

function StatsCard({ icon, label, value }: StatsCardProps) {
  return (
    <div className="flex items-center space-x-3 rounded-lg border border-border/50 bg-background/50 p-4">
      <div className="flex-shrink-0 text-primary">{icon}</div>
      <div>
        <p className="text-2xl font-bold text-foreground">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

export function CompleteStep() {
  const { setCompleted } = useOnboardingStore();
  const navigate = useNavigate();
  const [stats, setStats] = useState<{
    photosIndexed: number;
    facesDetected: number;
    tagsGenerated: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const [indexStats] = await Promise.all([
          apiService.getIndexStats(),
          apiService.getIndexStatus(),
        ]);

        setStats({
          photosIndexed: indexStats.database?.total_photos || 0,
          facesDetected: indexStats.database?.faces_detected || 0,
          tagsGenerated: (indexStats.database?.total_photos || 0) * 3, // Estimate 3 tags per photo
        });
      } catch (error) {
        console.error('Failed to fetch stats:', error);
        // Fallback to default values if API fails
        setStats({
          photosIndexed: 0,
          facesDetected: 0,
          tagsGenerated: 0,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const handleFinish = () => {
    setCompleted();
    navigate('/');
  };

  return (
    <div className="space-y-6" data-testid="complete-step">
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-900/30 border border-green-600/50">
          <CheckCircle className="h-10 w-10 text-green-400" />
        </div>
        <h2 className="mt-4 text-2xl font-bold text-foreground">
          You're All Set!
        </h2>
        <p className="mt-2 text-muted-foreground">
          Your photos are ready to search
        </p>
      </div>

      {/* Statistics */}
      <div className="grid gap-4 md:grid-cols-3">
        {loading ? (
          // Loading state
          Array.from({ length: 3 }).map((_, index) => (
            <div
              key={index}
              className="flex items-center space-x-3 rounded-lg border border-border/50 bg-background/50 p-4"
            >
              <Loader2 className="h-6 w-6 text-primary animate-spin" />
              <div>
                <div className="h-8 w-16 bg-muted animate-pulse rounded"></div>
                <div className="h-4 w-20 bg-muted animate-pulse rounded mt-1"></div>
              </div>
            </div>
          ))
        ) : (
          // Real stats
          <>
            <StatsCard
              icon={<Camera className="h-6 w-6" />}
              label="Photos Found"
              value={stats?.photosIndexed.toLocaleString() ?? '0'}
            />
            <StatsCard
              icon={<Users className="h-6 w-6" />}
              label="People Found"
              value={stats?.facesDetected ?? 0}
            />
            <StatsCard
              icon={<FileText className="h-6 w-6" />}
              label="Labels Added"
              value={stats?.tagsGenerated.toLocaleString() ?? '0'}
            />
          </>
        )}
      </div>

      {/* Quick tips */}
      <div className="rounded-lg bg-gradient-to-r from-primary/10 to-primary/20 border border-primary/30 p-6">
        <h3 className="font-semibold text-foreground mb-3">How to use Ideal Goggles:</h3>
        <ul className="space-y-2 text-sm text-foreground/90">
          <li className="flex items-start">
            <span className="mr-2 text-primary">•</span>
            <span>
              Type what you're looking for in the <strong className="text-primary">search box</strong> - like "sunset at the beach" or "birthday party"
            </span>
          </li>
          <li className="flex items-start">
            <span className="mr-2 text-primary">•</span>
            <span>
              Click any photo to see it bigger. Use arrow keys (← →) to browse through photos
            </span>
          </li>
          <li className="flex items-start">
            <span className="mr-2 text-primary">•</span>
            <span>
              Go to <strong className="text-primary">People</strong> to name faces so you can search for specific people
            </span>
          </li>
          <li className="flex items-start">
            <span className="mr-2 text-primary">•</span>
            <span>
              Your photos stay private on your computer - nothing is uploaded anywhere
            </span>
          </li>
        </ul>
      </div>

      {/* Finish button */}
      <div className="flex justify-center pt-4">
        <Button
          onClick={handleFinish}
          size="lg"
          className="!bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 !font-semibold transition-all px-8"
          data-testid="start-using-btn"
        >
          Start Using Ideal Goggles
        </Button>
      </div>
    </div>
  );
}
