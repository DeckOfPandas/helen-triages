source "https://rubygems.org"

gem "jekyll", "~> 4.3"
gem "jekyll-sitemap"

# DO NOT add the `github-pages` gem.
#
# It is only needed for GitHub Pages' CLASSIC branch-based build, and it pins
# Jekyll to 3.9 — which would silently downgrade this site from 4.3 and break
# things for no benefit.
#
# Deployment here runs `bundle exec jekyll build` in a GitHub Actions workflow
# (.github/workflows/build-and-deploy.yml), so the Jekyll version above is the
# one that is actually used. Plain `jekyll "~> 4.3"` is correct.
