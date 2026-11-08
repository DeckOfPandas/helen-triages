# Sourced by every interactive shell in the container, straight from the bind
# mount, so an edit here takes effect in the next shell with no rebuild.
#
# The two site servers. Each listens on 0.0.0.0 so the published port reaches
# it; the host sees the same numbers (kit.env PORTS).
alias jekyll-local='bundle exec jekyll serve --config _config.yml,_config_local.yml --port 5000 --host 0.0.0.0'
alias jekyll-prod='JEKYLL_ENV=production bundle exec jekyll serve --config _config.yml --port 5001 --host 0.0.0.0'
