/**
 * Test configuration and feature flags
 * Controls which tests should run based on available dependencies
 */

export interface TestConfig {
  // Core features that are always available
  core: {
    enabled: boolean;
    backend: boolean;
    frontend: boolean;
  };

  // Optional features that may require additional setup
  features: {
    ocr: boolean;
    faceSearch: boolean;
    semanticSearch: boolean;
    imageSearch: boolean;
    modelDependencies: boolean;
  };

  // Test environment settings
  environment: {
    ci: boolean;
    local: boolean;
    useExistingServer: boolean;
    skipHeavyTests: boolean;
    skipIntegrationTests: boolean;
  };

  // Performance settings
  performance: {
    timeout: number;
    retries: number;
    workers: number;
    parallel: boolean;
  };
}

/**
 * Check if a feature is available
 */
async function checkFeatureAvailability(): Promise<Partial<TestConfig['features']>> {
  const features: Partial<TestConfig['features']> = {};

  try {
    // Check for OCR dependencies
    const ocrCheck = await fetch('http://localhost:5555/health/features/ocr').catch(() => null);
    features.ocr = ocrCheck?.ok ?? false;

    // Check for face search dependencies
    const faceCheck = await fetch('http://localhost:5555/health/features/face-search').catch(() => null);
    features.faceSearch = faceCheck?.ok ?? false;

    // Check for semantic search dependencies
    const semanticCheck = await fetch('http://localhost:5555/health/features/semantic-search').catch(() => null);
    features.semanticSearch = semanticCheck?.ok ?? false;

    // Check for image search dependencies
    const imageCheck = await fetch('http://localhost:5555/health/features/image-search').catch(() => null);
    features.imageSearch = imageCheck?.ok ?? false;

    // Check for model dependencies
    features.modelDependencies = features.semanticSearch || features.imageSearch || features.faceSearch;
  } catch (error) {
    console.warn('Could not check feature availability:', error);
  }

  return features;
}

/**
 * Get the current test configuration
 */
export async function getTestConfig(): Promise<TestConfig> {
  const isCI = !!process.env.CI;
  const useExistingServer = !!process.env.USE_EXISTING_SERVER;
  const skipHeavy = !!process.env.SKIP_HEAVY_TESTS;
  const skipIntegration = !!process.env.SKIP_INTEGRATION_TESTS;

  const features = await checkFeatureAvailability();

  return {
    core: {
      enabled: true,
      backend: true,
      frontend: true,
    },
    features: {
      ocr: features.ocr ?? false,
      faceSearch: features.faceSearch ?? false,
      semanticSearch: features.semanticSearch ?? false,
      imageSearch: features.imageSearch ?? false,
      modelDependencies: features.modelDependencies ?? false,
    },
    environment: {
      ci: isCI,
      local: !isCI,
      useExistingServer,
      skipHeavyTests: skipHeavy,
      skipIntegrationTests: skipIntegration,
    },
    performance: {
      timeout: isCI ? 120000 : 60000,
      retries: isCI ? 2 : 0,
      workers: isCI ? 1 : undefined,
      parallel: !isCI,
    },
  };
}

/**
 * Skip test if feature is not available
 */
export function skipIfFeatureUnavailable(
  test: any,
  feature: keyof TestConfig['features'],
  config: TestConfig
) {
  if (!config.features[feature]) {
    test.skip(`Skipping: ${feature} feature is not available`);
  }
}

/**
 * Skip test in CI environment
 */
export function skipInCI(test: any, config: TestConfig) {
  if (config.environment.ci) {
    test.skip('Skipping: Test is disabled in CI');
  }
}

/**
 * Skip heavy tests if requested
 */
export function skipIfHeavy(test: any, config: TestConfig) {
  if (config.environment.skipHeavyTests) {
    test.skip('Skipping: Heavy test is disabled');
  }
}

/**
 * Skip integration tests if requested
 */
export function skipIfIntegration(test: any, config: TestConfig) {
  if (config.environment.skipIntegrationTests) {
    test.skip('Skipping: Integration test is disabled');
  }
}