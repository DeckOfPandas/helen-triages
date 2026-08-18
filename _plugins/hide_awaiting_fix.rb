# =============================================================================
# DO NOT PUBLISH A RECIPE THAT IS WAITING ON A FIX. GitHub issue #331.
# =============================================================================
# `meta.awaiting-fix: true` means "there is a known, open problem with this
# page". Such a page must not reach the live site -- but everything else must,
# because the alternative is holding the whole site back until every open issue
# is closed, which is how a site never ships.
#
# WHY THIS REMOVES THE DOCUMENT RATHER THAN HIDING IT FROM THE INDEX.
#
# Filtering the index listing is the obvious fix and it does not work. Issue
# #276 is the precedent, and it cost two pages: food/swatch.html and
# food/swatch-scribbles.html were internal references linked from nowhere on
# the site, and they were PUBLISHED ANYWAY, because Jekyll gives every document
# it renders a URL whether or not an <a href> points at it. UNLINKED IS NOT
# UNPUBLISHED. A recipe dropped from the index still sits at
# /food/recipes/<slug>/, still lands in sitemap.xml, and is still indexed by
# anything that reads the sitemap -- which is the one place you least want a
# page you have flagged as wrong.
#
# So the document is removed from its collection at :post_read, before any URL,
# sitemap entry or `site.food_recipes` listing exists. Nothing downstream has to
# remember to filter, which matters because "remember to filter" is exactly what
# failed last time.
#
# WHY A PLUGIN AND NOT `published: false` IN FRONT MATTER. Jekyll's own
# `published` key would do this, but it is a SECOND field saying the same thing
# as `meta.awaiting-fix`, and two fields that must agree will eventually
# disagree -- silently, and in the direction that publishes the broken page.
# One field, enforced in one place.
#
# Plugins run because .github/workflows/build-and-deploy.yml uses
# `bundle exec jekyll build` rather than the github-pages gem's safe mode. If
# that ever changes to a Pages-native build, THIS FILE STOPS RUNNING AND FAILS
# OPEN -- flagged recipes would publish with no error at all. tests/test_food.py
# asserts the workflow still uses a plugin-capable build for that reason.
# =============================================================================
Jekyll::Hooks.register :site, :post_read do |site|
  # Locally the flagged pages must stay visible: they are the ones being
  # worked on, and hiding them is the opposite of useful. _config_local.yml
  # sets this true; _config.yml sets it false, so production hides them.
  next if site.config["show_awaiting_fix"]

  hidden = []
  site.collections.each_value do |collection|
    collection.docs.reject! do |doc|
      meta = doc.data["meta"]
      flagged = meta.is_a?(Hash) && meta["awaiting-fix"] == true
      hidden << doc.relative_path if flagged
      flagged
    end
  end

  unless hidden.empty?
    # Announced, never silent. A page vanishing from a build is precisely the
    # kind of thing that should be impossible to do by accident, and the count
    # is the only evidence in the log that the gate did anything at all.
    Jekyll.logger.info "awaiting-fix:", "held back #{hidden.length} page(s) " \
                                        "-- #{hidden.join(', ')}"
  end
end
