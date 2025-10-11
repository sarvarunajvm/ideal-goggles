# Release Process

This document explains how to create and manage releases for ideal-goggles.

## Quick Release (Recommended)

To create a new release with automatic versioning:

```bash
# Patch version (1.0.24 -> 1.0.25)
pnpm run tag:patch

# Minor version (1.0.24 -> 1.1.0)
pnpm run tag:minor

# Major version (1.0.24 -> 2.0.0)
pnpm run tag:major
```

This will:
1. Update version in `package.json` and `backend/pyproject.toml`
2. Commit the version changes
3. Create a git tag
4. **Automatically push the tag and changes to remote**
5. Trigger the release workflow on GitHub Actions

## Manual Release

If you need to specify a custom version:

```bash
# Create and push a specific version
pnpm run tag 1.2.3
```

## Release Workflow

Once you push a tag, GitHub Actions automatically:

1. **Verifies CI Status**: Ensures Quick CI and E2E tests have passed
2. **Builds Packages**: Creates installers for all platforms
   - macOS: DMG (arm64)
   - Windows: NSIS installer and portable (x64, ia32)
   - Linux: AppImage and DEB (x64)
3. **Creates GitHub Release**: Publishes release with all artifacts

### Monitoring

Monitor the release process at:
- GitHub Actions: https://github.com/[owner]/ideal-goggles/actions
- Releases: https://github.com/[owner]/ideal-goggles/releases

## Manual Workflow Trigger

If you need to manually trigger a release build:

1. Go to GitHub Actions > Release workflow
2. Click "Run workflow"
3. **Required**: Enter the tag name (e.g., `v1.0.25`)
4. Optional: Skip CI checks (for testing only)

**Note**: The tag must exist before running manual workflow. Create it first:
```bash
git tag v1.0.25
git push origin v1.0.25
```

## Troubleshooting

### Release workflow not triggered automatically

**Cause**: Tag wasn't pushed to remote

**Solution**:
```bash
# Push the tag
git push origin v1.0.25

# Or use the convenience script
pnpm run release:push
```

### Manual build fails with "GitHub Releases requires a tag"

**Cause**: Trying to run workflow_dispatch without specifying a tag

**Solution**: When manually triggering, you must provide the tag name in the workflow inputs

### CI checks block release

**Cause**: Quick CI or E2E tests haven't passed for the tagged commit

**Solution**:
- Wait for CI to complete (workflow polls for up to 30 minutes)
- Or skip CI checks in manual trigger (testing only)

## Version Management

Current version is stored in two places:
- `package.json` (line 3)
- `backend/pyproject.toml`

Both are automatically updated by the release scripts. Do not modify manually.

## Release Checklist

Before creating a release:
- [ ] All changes committed and pushed
- [ ] CI tests passing on main branch
- [ ] Version number decided (patch/minor/major)
- [ ] Changelog or release notes prepared (optional - auto-generated)

After creating a release:
- [ ] Verify GitHub Actions workflow completes successfully
- [ ] Check GitHub release page for all platform artifacts
- [ ] Test download and installation of at least one artifact
