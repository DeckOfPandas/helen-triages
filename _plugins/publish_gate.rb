# The publish gate (#331, #667, #1137). A page reaches the live site only when
# its front matter says, as real booleans:
#
#     meta.awaiting_fix: false    both sites
#     meta.proofread:    true     both sites
#     meta.rewritten:    true     a cocktail only
#
# Anything else is held back: a flag missing, set the other way, spelled with a
# hyphen, or written as a string. The comparisons are strict (`== false`,
# `== true`) so that every way of getting a flag wrong fails closed.
# A held-back document is removed from its collection at :post_read, so it has
# no URL and no sitemap entry; leaving it out of an index would not unpublish it
# (#276). `show_awaiting_fix: true`, which only _config_local.yml sets, switches
# the whole gate off so that every page builds locally. DECISIONS §4.0.

# Plugins run only because the deploy uses `bundle exec jekyll build`. A
# Pages-native build would skip this file and publish everything, silently;
# tests/test_site_config.py::test_deploy_workflow_still_runs_a_plugin_capable_build
# guards that.

# Only the collections that publish are gated. Dev pages and drafts are kept off
# the site by `output: false`, and a dev page has no `meta`, so gating them would
# delete them. A gated collection's schema must allow every flag asked of it: the
# magic bag declares `awaiting_fix` and `proofread` (tests/test_magic_bag.py
# META_KEYS).
GATED_COLLECTIONS = %w[food_recipes food_magic_bag cocktail_recipes].freeze

Jekyll::Hooks.register :site, :post_read do |site|
  # _config_local.yml sets this true and _config.yml sets it false: locally the
  # held-back pages are the ones being worked on. The key is named for the first
  # flag and switches the whole gate.
  next if site.config["show_awaiting_fix"]

  hidden = []
  site.collections.each do |name, collection|
    # Scoped to GATED_COLLECTIONS: the rule below fails closed, so unscoped it
    # would remove every page that has no `meta`.
    next unless GATED_COLLECTIONS.include?(name)

    collection.docs.reject! do |doc|
      meta = doc.data["meta"]
      # Publish only on an explicit pass. A missing key, the hyphenated
      # `awaiting-fix` and the string "true" all hold the page back.
      unless meta.is_a?(Hash)
        hidden << "#{doc.relative_path} (no meta)"
        next true
      end

      reasons = []
      reasons << "awaiting_fix" unless meta["awaiting_fix"] == false
      reasons << "proofread"    unless meta["proofread"] == true

      # Cocktails only (#1137): `rewritten: true` says the prose is Helen's and not
      # the source's. `made_before` is deliberately not a leg; an unmade drink
      # publishes (#722).
      if name == "cocktail_recipes"
        reasons << "rewritten" unless meta["rewritten"] == true
      end

      # The log names each page and the flag that stopped it, because a bare count
      # does not say why an expected page is missing.
      hidden << "#{doc.relative_path} (#{reasons.join(', ')})" unless reasons.empty?
      !reasons.empty?
    end
  end

  unless hidden.empty?
    Jekyll.logger.info "publish gate:", "held back #{hidden.length} page(s) " \
                                        "-- #{hidden.join(', ')}"
  end
end
