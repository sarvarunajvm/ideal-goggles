#!/usr/bin/env node

const { execSync } = require('child_process');
const updateVersion = require('./update-version');

function exec(command, silent = false) {
  try {
    const output = execSync(command, { encoding: 'utf8' });
    if (!silent) console.log(output.trim());
    return output.trim();
  } catch (error) {
    console.error(`Failed to execute: ${command}`);
    console.error(error.message);
    process.exit(1);
  }
}

function createTag(version) {
  if (!version) {
    console.error('Usage: node create-tag.js <version>');
    console.error('Example: node create-tag.js 1.0.10');
    console.error('Example: node create-tag.js patch  (auto-increment patch version)');
    console.error('Example: node create-tag.js minor  (auto-increment minor version)');
    console.error('Example: node create-tag.js major  (auto-increment major version)');
    process.exit(1);
  }

  // Handle auto-increment
  if (['major', 'minor', 'patch'].includes(version)) {
    const currentVersion = require('../package.json').version;
    const [major, minor, patch] = currentVersion.split('.').map(Number);

    switch (version) {
      case 'major':
        version = `${major + 1}.0.0`;
        break;
      case 'minor':
        version = `${major}.${minor + 1}.0`;
        break;
      case 'patch':
        version = `${major}.${minor}.${patch + 1}`;
        break;
    }
    console.log(`Auto-incrementing to version ${version}`);
  }

  // Remove 'v' prefix if present
  version = version.replace(/^v/, '');

  // Validate version format
  if (!/^\d+\.\d+\.\d+(-[\w.]+)?$/.test(version)) {
    console.error(`Invalid version format: ${version}`);
    process.exit(1);
  }

  console.log(`\n🚀 Creating release ${version}\n`);

  // Step 1: Check for uncommitted changes
  const status = exec('git status --porcelain', true);
  if (status) {
    console.error('❌ You have uncommitted changes. Please commit or stash them first.');
    console.error('\nUncommitted files:');
    console.error(status);
    process.exit(1);
  }

  // Step 2: Update versions in all files
  console.log('📝 Updating version files...');
  updateVersion(version);

  // Step 3: Commit version changes
  console.log('\n📦 Committing version changes...');
  exec('git add package.json backend/pyproject.toml');

  // Check if any files are staged for commit; using name-only avoids non-zero exit codes
  const staged = exec('git diff --cached --name-only', true);
  if (staged && staged.trim().length > 0) {
    exec(`git commit -m "chore: release v${version}

Updated versions in:
- package.json
- backend/pyproject.toml"`);
  } else {
    console.log('ℹ️  No version changes needed');
  }

  // Step 4: Create git tag
  console.log('\n🏷️  Creating git tag...');
  const tagName = `v${version}`;

  try {
    exec(`git tag -a ${tagName} -m "Release ${tagName}"`);
    console.log(`✅ Created tag ${tagName}`);
  } catch (error) {
    if (error.message.includes('already exists')) {
      console.error(`❌ Tag ${tagName} already exists`);
      process.exit(1);
    }
    throw error;
  }

  // Step 5: Push tag and changes
  console.log('\n✨ Release prepared successfully!');
  console.log('\n📤 Pushing changes and tag to remote...');

  try {
    exec('git push origin main');
    exec(`git push origin ${tagName}`);
    console.log(`✅ Successfully pushed tag ${tagName} to remote`);
    console.log('\n🚀 GitHub Actions will now automatically:');
    console.log('   1. Run CI checks (Quick CI + E2E Tests)');
    console.log('   2. Build packages for all platforms');
    console.log('   3. Create a GitHub release with artifacts');
    console.log(`\n📊 Monitor progress at: https://github.com/${exec('git config --get remote.origin.url', true).replace(/.*github\.com[:/](.*)\.git/, '$1')}/actions`);
  } catch (error) {
    console.error('\n❌ Failed to push to remote');
    console.error('You can manually push with:');
    console.log(`   git push origin main && git push origin ${tagName}`);
    console.log('\nOr use:');
    console.log('   pnpm run release:push');
    process.exit(1);
  }
}

// Handle script execution
if (require.main === module) {
  const version = process.argv[2];
  createTag(version);
}
