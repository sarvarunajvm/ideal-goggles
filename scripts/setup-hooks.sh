#!/bin/bash

# Setup script for git hooks

HOOKS_DIR=".git/hooks"
SCRIPTS_DIR="scripts/git-hooks"

echo "🔧 Setting up git hooks..."

# Check if .git directory exists
if [ ! -d ".git" ]; then
  echo "❌ Not a git repository. Please run this from the project root."
  exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Install pre-commit hook
if [ -f "$SCRIPTS_DIR/pre-commit" ]; then
  cp "$SCRIPTS_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
  chmod +x "$HOOKS_DIR/pre-commit"
  echo "✅ Installed pre-commit hook"
else
  echo "⚠️  pre-commit hook not found"
fi

# Install pre-push hook
if [ -f "$SCRIPTS_DIR/pre-push" ]; then
  cp "$SCRIPTS_DIR/pre-push" "$HOOKS_DIR/pre-push"
  chmod +x "$HOOKS_DIR/pre-push"
  echo "✅ Installed pre-push hook"
else
  echo "⚠️  pre-push hook not found"
fi

# Note: Git doesn't have a post-tag hook, but we can use a custom workflow
echo ""
echo "📝 Note: To automatically update versions when creating a tag, use:"
echo "   pnpm run tag <version>"
echo ""
echo "This will:"
echo "1. Update all version files"
echo "2. Commit the changes"
echo "3. Create a git tag"
echo "4. Push both the commit and tag"

echo ""
echo "✅ Git hooks setup complete!"