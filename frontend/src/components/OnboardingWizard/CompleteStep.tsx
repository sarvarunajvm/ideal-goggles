import { useOnboardingStore } from '../../stores/onboardingStore';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Camera, Users, FileText } from 'lucide-react';

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

  // TODO: Fetch actual stats from API
  const stats = {
    photosIndexed: 500,
    facesDetected: 3,
    tagsGenerated: 1250,
  };

  const handleFinish = () => {
    setCompleted();
    navigate('/');
  };

  return (
    <div className="space-y-6">
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
        <StatsCard
          icon={<Camera className="h-6 w-6" />}
          label="Photos Found"
          value={stats.photosIndexed.toLocaleString()}
        />
        <StatsCard
          icon={<Users className="h-6 w-6" />}
          label="People Found"
          value={stats.facesDetected}
        />
        <StatsCard
          icon={<FileText className="h-6 w-6" />}
          label="Labels Added"
          value={stats.tagsGenerated.toLocaleString()}
        />
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
        <button
          onClick={handleFinish}
          className="rounded-lg px-8 py-3 font-semibold [background:var(--gradient-gold)] text-black shadow-lg shadow-primary/30 hover:shadow-xl hover:shadow-primary/40 hover:scale-[1.02] transition-all"
        >
          Start Using Ideal Goggles
        </button>
      </div>
    </div>
  );
}
