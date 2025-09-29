#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function updateVersion(version) {
  if (!version) {
    console.error('Usage: node update-version.js <version>');
    console.error('Example: node update-version.js 1.0.10');
    console.error('Or use with git tag: node update-version.js $(git describe --tags --abbrev=0)');
    process.exit(1);
  }

  // Remove 'v' prefix if present (e.g., v1.0.10 -> 1.0.10)
  version = version.replace(/^v/, '');

  // Validate version format
  if (!/^\d+\.\d+\.\d+(-[\w.]+)?$/.test(version)) {
    console.error(`Invalid version format: ${version}`);
    console.error('Expected format: X.Y.Z or X.Y.Z-suffix');
    process.exit(1);
  }

  console.log(`Updating all project versions to ${version}...`);

  const updates = [
    {
      file: 'package.json',
      type: 'json',
      path: ['version']
    },
    {
      file: 'frontend/package.json',
      type: 'json',
      path: ['version']
    },
    {
      file: 'tests/package.json',
      type: 'json',
      path: ['version']
    },
    {
      file: 'backend/pyproject.toml',
      type: 'toml',
      pattern: /^version = ".*"$/m,
      replacement: `version = "${version}"`
    }
  ];

  let successCount = 0;
  let errorCount = 0;

  updates.forEach(update => {
    const filePath = path.join(__dirname, '..', update.file);

    try {
      if (!fs.existsSync(filePath)) {
        console.warn(`⚠️  File not found: ${update.file}`);
        return;
      }

      let content = fs.readFileSync(filePath, 'utf8');
      let updated = false;

      if (update.type === 'json') {
        const data = JSON.parse(content);
        let current = data;

        // Navigate to nested property if needed
        for (let i = 0; i < update.path.length - 1; i++) {
          current = current[update.path[i]];
        }

        const oldVersion = current[update.path[update.path.length - 1]];
        current[update.path[update.path.length - 1]] = version;

        content = JSON.stringify(data, null, 2) + '\n';
        updated = oldVersion !== version;

        if (updated) {
          console.log(`✅ Updated ${update.file}: ${oldVersion} → ${version}`);
        } else {
          console.log(`✓  ${update.file} already at version ${version}`);
        }
      } else if (update.type === 'toml') {
        const oldContent = content;
        content = content.replace(update.pattern, update.replacement);
        updated = oldContent !== content;

        if (updated) {
          const oldVersion = oldContent.match(/version = "(.*?)"/)?.[1];
          console.log(`✅ Updated ${update.file}: ${oldVersion} → ${version}`);
        } else {
          console.log(`✓  ${update.file} already at version ${version}`);
        }
      }

      if (updated) {
        fs.writeFileSync(filePath, content);
        successCount++;
      }
    } catch (error) {
      console.error(`❌ Error updating ${update.file}: ${error.message}`);
      errorCount++;
    }
  });

  console.log(`\n📊 Summary: ${successCount} files updated, ${errorCount} errors`);

  if (errorCount > 0) {
    process.exit(1);
  }
}

// Handle script execution
if (require.main === module) {
  const version = process.argv[2];

  // If no version provided, try to get from latest git tag
  if (!version) {
    try {
      const latestTag = execSync('git describe --tags --abbrev=0 2>/dev/null', { encoding: 'utf8' }).trim();
      if (latestTag) {
        console.log(`Using latest git tag: ${latestTag}`);
        updateVersion(latestTag);
      } else {
        console.error('No version provided and no git tags found');
        process.exit(1);
      }
    } catch (error) {
      console.error('No version provided and unable to get git tag');
      console.error('Usage: node update-version.js <version>');
      process.exit(1);
    }
  } else {
    updateVersion(version);
  }
}

module.exports = updateVersion;