import { useOnboardingStore } from '../../stores/onboardingStore';
import { Search, Users, Lock, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';

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
    <div className="space-y-6" data-testid="welcome-step">
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
        <Button
          onClick={handleSkip}
          className="!bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !border-[rgb(var(--red-rgb))]/50 !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] hover:scale-105 !font-semibold transition-all"
          data-testid="skip-onboarding-btn"
        >
          Skip setup
        </Button>
        <Button
          onClick={nextStep}
          className="!bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 !font-semibold transition-all"
          data-testid="get-started-btn"
        >
          Get Started
        </Button>
      </div>
    </div>
  );
}
