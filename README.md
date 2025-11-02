# Ideal Goggles User Guide Branch

This branch contains only the user manual for GitHub Pages deployment.

## GitHub Pages Setup

This branch is configured to work with GitHub Pages using Jekyll:

1. **Jekyll Configuration**: `_config.yml` sets up the Cayman theme
2. **Index Page**: `index.md` contains the full user manual (Jekyll converts to HTML)
3. **Original Manual**: `USER_MANUAL.md` kept for reference

## Deployment

To deploy on GitHub Pages:

1. Go to repository Settings → Pages
2. Source: Deploy from branch
3. Branch: `user_guide`
4. Folder: `/docs`
5. Save

GitHub will automatically:
- Convert `index.md` to HTML using Jekyll
- Apply the Cayman theme
- Make it available at: `https://[username].github.io/ideal-goggles/`

## Local Preview

To preview locally with Jekyll:

```bash
cd docs
gem install bundler jekyll
bundle exec jekyll serve
```

Visit: http://localhost:4000

## File Structure

```
docs/
├── _config.yml       # Jekyll configuration (theme, title)
├── index.md          # Main user manual (auto-converted to HTML)
└── USER_MANUAL.md    # Original markdown (for reference)
```

## How It Works

GitHub Pages with Jekyll:
- Automatically processes `.md` files to HTML
- Applies the theme specified in `_config.yml`
- No need for manual `index.html` creation
- Supports all markdown features + syntax highlighting
