# What a card's ingredient line says, and in what order (#567, #640, #691).
#
# Tiers, from #567:
#   1  base spirits                 2  liqueurs, amari, fortified, wine
#   3  citrus, then other juices    4  syrups, honeys, sugars
#   5  anything else                6  bitters
#   7  floats, rinses and shells, from `as:` (#754)
# Within a tier, largest volume first; ties keep the recipe's own order.
# `card_order: <n>` on an ingredient replaces its tier; 0 is legal and means
# before everything, so test for nil and not for truthiness.
# `as: muddle` is recorded on drinks and deliberately sorts nothing: grouping
# muddled ingredients first put the base spirit last on several drinks.

require_relative "amount"

module HelenTriages
  class CocktailCardIngredients < Jekyll::Generator
    safe true
    # After cocktail_costs and cocktail_units, which are :normal. A presentation
    # step: the arithmetic plugins must never read its output back.
    priority :low

    COLLECTIONS = %w[cocktail_recipes cocktail_drafts].freeze

    # Which section of ingredients.yml puts a generic in which tier. The
    # sections are the classifier: do not add a second list here. A generic in no
    # listed section gets a build warning and fails
    # test_every_poured_generic_has_a_tier. `wine_and_sparkling` is tier 2, not 5:
    # champagne is alcohol and is what a French 75 tastes of.
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

    # Citrus before the other juices: tier 3's own order (#567), which volume
    # would get wrong (a Painkiller pours more pineapple than orange). Quoted,
    # not `%w[]`: every name has a space in it, and
    # test_the_citrus_that_sorts_first_is_juice_that_exists reads this literal.
    CITRUS = [
      "lime juice", "lemon juice", "orange juice", "grapefruit juice"
    ].freeze

    # A generic nothing classifies. Tier 5 rather than last, so an unclassified
    # ingredient lands among the odds and ends instead of after the bitters --
    # and the warning below is what actually gets it fixed.
    UNKNOWN_TIER = 5

    # `as:` values that sort after everything else on the card, because they
    # are added outside the main build (#567 tier 7; `shell` is #1256). `muddle`
    # is deliberately not here.
    LAST_TIER = 7
    SORTS_LAST = %w[float rinse shell].freeze

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

    # Millilitres for a pour, or 0 for anything not measured by volume: this is
    # a sort key, not arithmetic. A `(top)` is 0 too, since a topper's volume
    # belongs to the glass and not to the recipe.
    def volume_ml(amount)
      Amount.millilitres(amount, @per_ml, @ignored) || 0.0
    end

    # Each generic prints its card name, or itself where it has none. A list
    # generic means "either would do" (#441) and joins with " or "; the joined
    # string is then looked up in `card_name_joins`, where a pair that reads
    # badly is worded by hand. Falls back to `item` when there is no generic.
    def label_for(generics, item)
      label = generics.map { |g| @card_names[g] || g }.join(" or ")
      label = @joins[label] if @joins[label]
      label.to_s.empty? ? item.to_s : label
    end

    # `|`-separated: the generic, its card name and the suggestion for one
    # ingredient, so a filter can ask about this ingredient without a substring
    # match crossing into the next one.
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

        # Hidden only when every generic is hidden: "raw sugar or molasses sugar"
        # is one ingredient with two acceptable answers.
        next if generics.any? && generics.all? { |g| @hidden.include?(g) }

        label = label_for(generics, ing["item"])
        next if label.to_s.empty?

        # `card_order:` wins over `as:`, which wins over the generic's tier.
        use = ing["as"].to_s
        tier = if ing["card_order"]
                 ing["card_order"]
               elsif SORTS_LAST.include?(use)
                 LAST_TIER
               else
                 generics.map { |g| tier_for(g, unclassified) }.min
               end

        rows << {
          "label"  => label,
          "search" => search_key(generics, Array(ing["suggestion"]).map(&:to_s)),
          # A pure sort key, never rendered. Kept on the row so a test can
          # read back what the plugin decided without re-deriving it.
          "tier"   => tier,
          "ml"     => volume_ml(ing["amount"]),
          "citrus" => generics.any? { |g| CITRUS.include?(g) } ? 0 : 1,
          "index"  => index,
          # How many generics earned this label (#1051): 2+ when `label_for`
          # joined a list. Lets cocktails/search.json tell a joined label apart
          # without parsing it for " or ".
          "generics" => generics.length,
          # The label in the pieces a filter can apply (#1130): one per visible
          # generic. Not `label` split on " or ": `card_name_joins` rewrites the
          # joined string, so a split piece need not be a chip. Hidden generics
          # are left out; with none left it falls back to the label.
          "search_labels" => (
            visible = generics.reject { |g| @hidden.include?(g) }
                              .map { |g| @card_names[g] || g }
            visible.empty? ? [label] : visible
          )
        }
      end

      # `-ml` for descending volume, `index` last: sort_by is not stable, so the
      # original position is carried to keep ties in the recipe's own order.
      rows.sort_by { |r| [r["tier"], r["citrus"], -r["ml"], r["index"]] }
    end

    # A list generic takes the strongest tier of its options (`min` in
    # `card_rows`).
    def tier_for(generic, unclassified)
      tier = @tier_of[generic]
      return tier if tier
      unclassified << generic
      UNKNOWN_TIER
    end
  end
end
