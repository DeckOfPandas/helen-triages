# =============================================================================
# THE PUBLICATION GATE. TWO FLAGS, BOTH REQUIRED. Issues #331 and #667.
# =============================================================================
# A page reaches the live site only when it says BOTH:
#
#     meta.awaiting_fix: false     -- no known, open problem with this page
#     meta.proofread:    true      -- Helen has read what is now in the file
#
# Anything else is held back. This file was `hide_awaiting_fix.rb` until
# 2026-09-02 and gated on the first flag alone; it was renamed when the second
# joined, because a name that describes half a rule is worse than no name.
#
# WHAT EACH FLAG MEANS, because they are easy to read as the same thing.
#
# `awaiting_fix: true` does NOT mean "unfinished". Helen, 2026-09-01: "'awaiting
# fix' means I've proofread, but one small thing has been raised as a ticket,
# meaning that once that's fixed I can look for just that one thing rather than
# having to read the entire file again carefully." It is a bookmark in her own
# review. `proofread` is the review itself: whether the last human judgement
# still covers the bytes in the file. An agent editing one word invalidates the
# proofread and says nothing at all about whether a ticket is open.
#
# WHY THE SECOND FLAG IS NOT THE MISTAKE THE `published:` PARAGRAPH BELOW WARNS
# ABOUT. That paragraph refuses a Jekyll `published:` key because it would be a
# SECOND FIELD SAYING THE SAME THING as `meta.awaiting_fix` -- two fields, one
# meaning, and two fields that must agree will eventually disagree, silently and
# in the direction that publishes the broken page. That argument stands, and it
# is the reason there is still no `published:` key anywhere in this repo.
#
# `proofread` is not that case. It is a DIFFERENT FACT, held by a different
# person for a different reason, and the two are routinely in different states:
# a page can be proofread and ticketed (`proofread: true, awaiting_fix: true`),
# or clear of tickets and unread since an agent touched it (`awaiting_fix:
# false, proofread: false`). Neither value can be derived from the other, so
# requiring both is not duplication -- it is two conditions, both of which
# genuinely have to hold. Helen ruled it 2026-09-02: proofread "is the very last
# touch that I, the human, make to the file", and a page must not publish while
# it is false.
#
# THE COST, PAID KNOWINGLY. Five food recipes were live at `awaiting_fix: false,
# proofread: false` when this landed -- wagamama-yakitori-sauce, youvetsi,
# sweet-potato-chocolate-brownies, wagamama-teriyaki-sauce,
# duck-a-lorange-sanguine -- and this gate takes them off the live site until
# Helen proofreads them. That is the point of the change rather than a
# side-effect of it.
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
# `published` key would do this, but it is a SECOND FIELD SAYING THE SAME THING
# as `meta.awaiting_fix`, and two fields that must agree will eventually
# disagree -- silently, and in the direction that publishes the broken page.
# One field per fact, enforced in one place.
#
# Plugins run because .github/workflows/build-and-deploy.yml uses
# `bundle exec jekyll build` rather than the github-pages gem's safe mode. If
# that ever changes to a Pages-native build, THIS FILE STOPS RUNNING AND FAILS
# OPEN -- flagged recipes would publish with no error at all. tests/test_food.py
# asserts the workflow still uses a plugin-capable build for that reason.
# =============================================================================
# The collections whose documents are gated. Everything else -- dev pages,
# drafts -- has its own `output: false` protection, so gating them would simply
# delete them.
#
# food_magic_bag joined on 2026-08-26 with the collection itself. It is
# `output: true`, so every entry gets a real URL and a sitemap entry the moment
# the file exists -- which is exactly the condition this gate is for, and the
# reason "it's only a short one, it can't really be broken" is not an argument
# for leaving it out. A magic-bag entry declares the gate flags like a recipe
# and is held back on anything other than an explicit pass, same as everything
# else here.
#
# THE MAGIC BAG'S SCHEMA GREW A `proofread` FLAG THE SAME DAY THE SECOND LEG
# ARRIVED, 2026-09-02, and the order of events is worth keeping. Its schema was
# `meta: {awaiting_fix}` and nothing else -- deliberately, because `rewritten`
# and `proofread` were "recipe flags with no meaning here". The moment
# `proofread == true` became a leg of this gate, that stopped being true: a
# gate asking for a key a collection's schema forbids is a deletion, not a
# gate, and the one magic-bag entry vanished from the production build. Helen's
# ruling: the magic bag must be able to publish, `proofread` is required there
# too, it arrives `false` by default like everything else at ingest, and she
# flips it when she has read the built page. `rewritten` stays out -- there is
# no source to rewrite from. tests/test_magic_bag.py's META_KEYS is the schema.
GATED_COLLECTIONS = %w[food_recipes food_magic_bag cocktail_recipes].freeze

Jekyll::Hooks.register :site, :post_read do |site|
  # Locally the flagged pages must stay visible: they are the ones being
  # worked on, and hiding them is the opposite of useful. _config_local.yml
  # sets this true; _config.yml sets it false, so production hides them.
  #
  # The key is still named `show_awaiting_fix` although it now governs both
  # legs of the gate. Renaming it would mean changing two configs, two tests
  # and every mention in the handover for no behavioural gain, and the two
  # legs have never been separately switchable.
  next if site.config["show_awaiting_fix"]

  hidden = []
  site.collections.each do |name, collection|
    # SCOPED, and not scoping it would take the site down. The rule below is
    # FAIL CLOSED -- publish only on an explicit pass -- and `dev` pages carry
    # no `meta` block at all, so an unscoped version would hold back every one
    # of them. Only the collections that actually publish are gated.
    #
    # Cocktail DRAFTS carry all three flags since the 2026-09-02 migration
    # (#668), so the older version of this comment -- "cocktail pages carry no
    # flag" -- is no longer true of them. They are still not gated, because
    # `output: false` already keeps them off the site and a draft has no
    # publication to gate.
    next unless GATED_COLLECTIONS.include?(name)

    collection.docs.reject! do |doc|
      meta = doc.data["meta"]
      # PUBLISH ONLY ON AN EXPLICIT PASS: `awaiting_fix` exactly `false` AND
      # `proofread` exactly `true`. Anything else is held back -- a flag set the
      # wrong way, a flag missing entirely, a flag left under its old hyphenated
      # name, or a value that is a string rather than a boolean.
      #
      # Helen's call, 2026-08-18 for the first flag, and it inverts the original
      # default. The first version published unless it saw `true`, which fails
      # OPEN: every way of getting the flag wrong ended with the page live. A
      # missing key and a deliberate `false` were indistinguishable, and
      # `awaiting_fix: "true"` published the page you had just flagged.
      #
      # Failing closed makes every one of those loud instead. The cost is that a
      # new recipe does not publish until someone writes `awaiting_fix: false`
      # and Helen writes `proofread: true`, which is the right cost: this is the
      # gate that decides what the world sees.
      unless meta.is_a?(Hash)
        hidden << "#{doc.relative_path} (no meta)"
        next true
      end

      reasons = []
      reasons << "awaiting_fix" unless meta["awaiting_fix"] == false
      reasons << "proofread"    unless meta["proofread"] == true

      # NAMED, NOT COUNTED. The log line is the only evidence in the build that
      # the gate did anything, and "held back 6 pages" leaves you diffing front
      # matter to find out why. Which flag stopped which page is the whole
      # question when a page you expected to be live is not.
      hidden << "#{doc.relative_path} (#{reasons.join(', ')})" unless reasons.empty?
      !reasons.empty?
    end
  end

  unless hidden.empty?
    # Announced, never silent. A page vanishing from a build is precisely the
    # kind of thing that should be impossible to do by accident.
    Jekyll.logger.info "publish gate:", "held back #{hidden.length} page(s) " \
                                        "-- #{hidden.join(', ')}"
  end
end
