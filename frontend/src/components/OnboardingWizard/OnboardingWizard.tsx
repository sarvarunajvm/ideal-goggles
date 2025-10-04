import { useEffect } from 'react';
import { useOnboardingStore } from '../../stores/onboardingStore';
import { WelcomeStep } from './WelcomeStep';
import { FolderSelectionStep } from './FolderSelectionStep';
import { IndexingStep } from './IndexingStep';
import { CompleteStep } from './CompleteStep';
import { motion, AnimatePresence } from 'framer-motion';

const TOTAL_STEPS = 4;

export function OnboardingWizard() {
  const { currentStep, completed } = useOnboardingStore();

  // Disable body scroll while the onboarding wizard is visible
  useEffect(() => {
    const prevOverflow = document.body.style.overflow;
    const prevTouchAction = (document.body.style as any).touchAction;
    document.body.style.overflow = 'hidden';
    (document.body.style as any).touchAction = 'none';

    return () => {
      document.body.style.overflow = prevOverflow;
      (document.body.style as any).touchAction = prevTouchAction || '';
    };
  }, []);

  // Don't show wizard if already completed
  if (completed) {
    return null;
  }

  const stepVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 300 : -300,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction < 0 ? 300 : -300,
      opacity: 0,
    }),
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <WelcomeStep key="welcome" />;
      case 1:
        return <FolderSelectionStep key="folders" />;
      case 2:
        return <IndexingStep key="indexing" />;
      case 3:
        return <CompleteStep key="complete" />;
      default:
        return <WelcomeStep key="welcome" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4 overflow-hidden">
      <div className="w-full max-w-3xl rounded-lg bg-card border border-border/50 p-6 shadow-2xl my-auto max-h-[90vh] flex flex-col overflow-hidden">
        {/* Progress indicator */}
        <div className="mb-6">
          <div className="flex items-center justify-center">
            {Array.from({ length: TOTAL_STEPS }).map((_, index) => (
              <div
                key={index}
                className="flex items-center"
              >
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full transition-all ${
                    index <= currentStep
                      ? 'bg-primary text-primary-foreground shadow-md shadow-primary/25'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {index + 1}
                </div>
                {index < TOTAL_STEPS - 1 && (
                  <div
                    className={`h-1 w-16 transition-all ${
                      index < currentStep ? 'bg-primary' : 'bg-muted'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="mt-2 text-center text-sm text-muted-foreground">
            Step {currentStep + 1} of {TOTAL_STEPS}
          </div>
        </div>

        {/* Step content with animations */}
        <div className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait" custom={currentStep}>
            <motion.div
              key={currentStep}
              custom={currentStep}
              variants={stepVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{
                x: { type: 'spring', stiffness: 300, damping: 30 },
                opacity: { duration: 0.2 },
              }}
            >
              {renderStep()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
