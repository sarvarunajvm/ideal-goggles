import { useOnboardingStore } from '../../stores/onboardingStore';
import { Search, Users, Lock, Zap } from 'lucide-react';

export function WelcomeStep() {
  const { nextStep, setSkipOnboarding } = useOnboardingStore();

  const features = [
    {
      icon: <Search className="h-6 w-6" />,
      title: 'Smart Search',
      description: 'Find any photo by describing what you remember about it',
    },
    {
      icon: <Users className="h-6 w-6" />,
      title: 'Find People',
      description: 'Quickly find all photos of specific people',
    },
    {
      icon: <Lock className="h-6 w-6" />,
      title: 'Your Privacy Matters',
      description: 'Everything stays on your computer - nothing goes online',
    },
    {
      icon: <Zap className="h-6 w-6" />,
      title: 'Super Fast',
      description: 'Search through thousands of photos instantly',
    },
  ];

  const handleSkip = () => {
    setSkipOnboarding(true);
    // User can manually start indexing later from settings
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-foreground">
          Welcome to Ideal Goggles
        </h1>
        <p className="mt-2 text-lg text-muted-foreground">
          Find any photo in seconds, just by describing it
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="flex items-start space-x-3 rounded-lg border border-border/50 bg-background/50 p-4 hover:border-primary/30 transition-all"
          >
            <div className="flex-shrink-0 text-primary">{feature.icon}</div>
            <div>
              <h3 className="font-semibold text-foreground">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-4">
        <button
          onClick={handleSkip}
          className="rounded-lg px-6 py-2 text-sm font-medium [background:var(--gradient-red)] text-white shadow-md shadow-red-500/30 hover:shadow-lg hover:shadow-red-500/40 hover:scale-[1.02] transition-all"
        >
          Skip setup
        </button>
        <button
          onClick={nextStep}
          className="rounded-lg px-6 py-2 font-semibold [background:var(--gradient-gold)] text-black shadow-md shadow-primary/30 hover:shadow-lg hover:shadow-primary/40 hover:scale-[1.02] transition-all"
        >
          Get Started
        </button>
      </div>
    </div>
  );
}
