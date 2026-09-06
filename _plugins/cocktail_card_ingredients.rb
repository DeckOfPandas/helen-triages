# =============================================================================
# WHAT A CARD'S INGREDIENT LINE SAYS, AND IN WHAT ORDER. Issues #567, #640, #691.
# =============================================================================
# Helen, on #691: "e.g. seeing 'mint' first in a mastiha mojito takes a minute!
# We already do this on the food site." The food site does it with
# `_data/food/pantry.yml`, which sinks 34 staples to the end of a row; this is
# the same idea with the ORDER of everything else settled as well, because a
# drink's ingredients have a natural hierarchy that a dish's do not.
#
# WHY A PLUGIN AND NOT LIQUID, which is the same answer cocktail_costs.rb gives.
# The line this replaces was ONE 1,400-character Liquid statement doing four
# jobs at once -- hiding, labelling, joining and emitting search data -- and it
# was already at the edge of what anybody could read. Adding a seven-tier sort
# and a per-drink override to it in a language with no sort-by-computed-key
# would have produced something nobody could ever change again. Every comment
# from that line is preserved below, at the step it describes.
#
# --- THE ORDER, WHICH IS HELEN'S, FROM #567 ----------------------------------
# She wrote it as seven tiers and predicted her own preference:
#
#   1  higher-proof spirits          the base spirits: rum, gin, whisky,
#                                    brandy, agave, vodka, arrack, cachaca
#   2  lower-proof spirits           liqueurs, amari, vermouth and sherry,
#                                    wine and sparkling
#   3  citrus, then other juices     and the split within the tier is real:
#                                    lime and lemon before pineapple
#   4  sugar syrups                  syrups, honeys and sugars
#   5  anything else                 fruit, herbs, dairy, coconut cream, soda
#   6  bitters
#   7  floats                        NOT IMPLEMENTED -- see below
#
# WITHIN A TIER, LARGEST VOLUME FIRST. Helen ruled on the tie-break directly on
# 2026-09-06, choosing "volume, with a per-drink override field" over "most
# typifying the drink" -- which would have been truer and would have needed a
# judgement recorded on all 124 drinks, making it her worklist rather than a
# rule. Volume is computed from the data that is already there, so every drink
# orders itself and nothing has to be maintained.
#
# TIES INSIDE A TIER KEEP THE RECIPE'S OWN ORDER. A Last Word is three equal
# pours and a Negroni is three equal pours; there is no fact to sort them by, so
# the order Helen typed stands. That is #567's option (c) doing exactly the job
# she ranked it for -- last, and only where the first two say nothing.
#
# --- TIER 7 IS NOT BUILT, AND COULD NOT BE -----------------------------------
# A float is not recorded anywhere. Three drinks mention one -- tiki-max,
# zombie-intoxica and modern-zombie -- and all three do it in QQ PROSE, not in a
# field. There is nothing to read. #567's "unless floated" and its muddle-
# grouping rule are in the same position and for the same reason. Raised as its
# own issue rather than guessed at: a float is a small pour of something strong,
# so tier 1 currently puts it near the bottom of the spirits, which is wrong but
# is at least wrong in a way the ordering rule explains.
#
# --- THE OVERRIDE, WHICH EXISTS AND HAS NO USERS YET -------------------------
# An ingredient may carry `card_order: <n>`, and it replaces that entry's TIER.
# The number space is the tier space, so `card_order: 1` means "sort this with
# the base spirits" and `card_order: 9` means "after everything". Volume still
# breaks ties within the new tier.
#
# NO DRINK USES IT TODAY and that is deliberate rather than an oversight. Helen
# asked for the field so that a drink whose small pour IS the drink can be
# fixed when she notices one; inventing which drinks those are would be making
# exactly the judgement she declined to hand over. The field is built, tested
# against a fixture, and waiting.
# =============================================================================

module HelenTriages
  class CocktailCardIngredients < Jekyll::Generator
    safe true
    # AFTER cocktail_costs AND cocktail_units, both of which are :normal. This
    # one only reads `ingredients`, so the order does not actually matter today
    # -- :low is here to say that it is a PRESENTATION step and must never
    # become something the arithmetic plugins read back.
    priority :low

    COLLECTIONS = %w[cocktail_recipes cocktail_drafts].freeze

    # Which section of ingredients.yml puts a generic in which tier.
    #
    # THE SECTIONS ARE THE CLASSIFIER AND THAT IS THE POINT. Every generic is
    # declared in exactly one of these blocks already, by Helen, and the blocks
    # are the vocabulary's own idea of what kind of thing something is. Writing
    # a second classification here -- a list of "these are the strong ones" --
    # would be a second truth that drifts the first time a generic is added to
    # ingredients.yml and not to this file. Instead, a generic in NO listed
    # section is a build-time warning and a test failure.
    #
    # `wine_and_sparkling` IS TIER 2 AND NOT TIER 5, which is worth stating
    # because champagne is usually a topper. It is alcohol, it is the thing a
    # French 75 tastes of, and #567's tier 2 is "lower-proof spirits" -- an
    # 11% prosecco belongs there far more than beside the soda water.
    TIERS = {
      1 => %w[rum_styles gin_styles whisky_styles agave_styles brandy_styles
              cane_and_palm_spirits other_base_spirits],
      2 => %w[liqueurs herbal_liqueurs amari fortified_and_aromatised
              wine_and_sparkling],
      3 => %w[juices],
      4 => %w[syrups honeys sugars],
      5 => %w[fruit_and_herbs other],
      6 => %w[bitters]
    }.freeze

    # CITRUS BEFORE THE REST OF THE JUICES, which is tier 3's own internal
    # order and is stated separately because it is the one place #567 splits a
    # tier: "citrus then other juices". Volume would get this wrong regularly --
    # a Painkiller pours more pineapple than orange, and the drink is still a
    # citrus drink first.
    # Quoted rather than `%w[]`: every name here has a space in it, and `%w`
    # needs each one backslash-escaped, which reads like a typo and parses like
    # one too -- `test_the_citrus_that_sorts_first_is_juice_that_exists` read
    # `lime\ juice` as "lime" and "juice" the first time it ran.
    CITRUS = [
      "lime juice", "lemon juice", "orange juice", "grapefruit juice"
    ].freeze

    # A generic nothing classifies. Tier 5 rather than last, so an unclassified
    # ingredient lands among the odds and ends instead of after the bitters --
    # and the warning below is what actually gets it fixed.
    UNKNOWN_TIER = 5

    def generate(site)
      vocab = site.data.dig("cocktails", "ingredients")
      return unless vocab

      @card_names = vocab["card_names"] || {}
      @joins      = vocab["card_name_joins"] || {}
      @hidden     = (vocab["not_on_cards"] || []).to_a
      @per_ml     = vocab.dig("measures", "per_ml") || {}
      @ignored    = vocab.dig("measures", "ignored_words") || []

      @tier_of = {}
      TIERS.each do |tier, sections|
        sections.each do |section|
          Array(vocab[section]).each { |g| @tier_of[g.to_s] = tier }
        end
      end

      unclassified = []
      COLLECTIONS.each do |key|
        next unless site.collections[key]
        site.collections[key].docs.each do |doc|
          rows = card_rows(doc.data["ingredients"], unclassified)
          doc.data["card_ingredients"] = rows
        end
      end

      unless unclassified.empty?
        Jekyll.logger.warn "Cards:", "no ingredients.yml section classifies " \
          "#{unclassified.uniq.sort.join(', ')} -- ordered as tier " \
          "#{UNKNOWN_TIER}. See _plugins/cocktail_card_ingredients.rb."
      end
      Jekyll.logger.info "Cards:", "ordered ingredient lines for " \
        "#{COLLECTIONS.sum { |k| site.collections[k]&.docs&.size.to_i }} drinks"
    end

    private

    # Millilitres for a pour, or 0 for anything not measured by volume.
    #
    # ZERO RATHER THAN NIL, because this is a SORT key and not arithmetic. A
    # dash of bitters and a mint sprig genuinely have no volume to compare, and
    # they are already in tiers 5 and 6 where nothing else is competing with
    # them. `to top` is 0 for the same reason: a topper's volume is a property
    # of the glass, not of the recipe, so ranking it against a measured pour
    # would be comparing two different kinds of number.
    def volume_ml(amount)
      a = amount.to_s.strip
      m = /\A([\d.]+)\s+(.*)\z/.match(a) or return 0.0
      unit = m[2].strip
      @ignored.each { |w| unit = unit.sub(/\A#{Regexp.escape(w)}\s+/, "") }
      return 0.0 unless @per_ml.key?(unit)
      m[1].to_f * @per_ml[unit].to_f
    end

    # SUBSTITUTE ONLY IF EVERY GENERIC HAS A CARD NAME. A list generic means
    # "either would do" (#441) and ten rum entries carry one, so they join with
    # the same italic-free " or " the drink page uses. A list mixing a named rum
    # with something unnamed would otherwise print half a fact; there is no such
    # entry today, and this is what stops one appearing silently.
    #
    # THE JOIN IS THEN LOOKED UP in `card_name_joins`, because a pair sharing a
    # head word reads badly and no rule collapses it well: `Demerara overproof
    # rum or Demerara rum` is Helen's `Demerara rum or overproof`, which drops
    # two words from the second option and reorders the pair. Absent means the
    # default join stands, which is the case for six of the seven pairs.
    def label_for(generics, item)
      label = generics.map { |g| @card_names[g] || g }.join(" or ")
      label = @joins[label] if @joins[label]
      label.to_s.empty? ? item.to_s : label
    end

    # `data-ing` IS `|`-SEPARATED, the same self-delimiting shape
    # data-ingredients uses on the card and food/index.html's
    # data-all-ingredients uses on a recipe row. It carries the generic, its
    # card name and the suggestion for ONE ingredient, so the script can ask
    # "does this ingredient answer the chip?" without a substring probe that
    # could match across the seam between two of them.
    def search_key(generics, suggestions)
      parts = []
      generics.each do |g|
        parts << g
        parts << @card_names[g] if @card_names[g]
      end
      parts.concat(suggestions)
      parts.join("|").downcase
    end

    def card_rows(ingredients, unclassified)
      return [] unless ingredients.is_a?(Array)

      rows = []
      ingredients.each_with_index do |ing, index|
        next unless ing.is_a?(Hash)

        generics = Array(ing["generic"]).map(&:to_s)

        # HIDDEN ONLY WHEN EVERY GENERIC IS HIDDEN. An entry offering "raw sugar
        # or molasses sugar" is one ingredient with two acceptable answers, and
        # it disappears only if the card would decline both. The same rule the
        # Liquid used, kept exactly.
        next if generics.any? && generics.all? { |g| @hidden.include?(g) }

        label = label_for(generics, ing["item"])
        next if label.to_s.empty?

        tier = ing["card_order"] || generics.map { |g| tier_for(g, unclassified) }.min
        rows << {
          "label"  => label,
          "search" => search_key(generics, Array(ing["suggestion"]).map(&:to_s)),
          # A pure sort key, never rendered. Kept on the row so a test can read
          # back what the plugin decided without re-deriving it.
          "tier"   => tier,
          "ml"     => volume_ml(ing["amount"]),
          "citrus" => generics.any? { |g| CITRUS.include?(g) } ? 0 : 1,
          "index"  => index
        }
      end

      # `-ml` FOR DESCENDING VOLUME, `index` LAST TO KEEP TIES STABLE. Ruby's
      # sort_by is not guaranteed stable, so the original position is carried
      # explicitly rather than relied upon -- which is what makes "ties keep the
      # recipe's own order" a promise instead of an accident.
      rows.sort_by { |r| [r["tier"], r["citrus"], -r["ml"], r["index"]] }
    end

    # A LIST GENERIC TAKES THE STRONGEST TIER OF ITS OPTIONS, via `min` above.
    # "aguardiente or kirschwasser" is two brandies and lands in tier 1 either
    # way; the rule matters for a pair that crosses a boundary, where sorting by
    # the more prominent of the two answers is the reading that matches how the
    # entry is offered -- "either would do" means the drink is at least the
    # better one.
    def tier_for(generic, unclassified)
      tier = @tier_of[generic]
      return tier if tier
      unclassified << generic
      UNKNOWN_TIER
    end
  end
end
