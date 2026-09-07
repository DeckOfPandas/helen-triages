# =============================================================================
# WHAT A FOOD RECIPE CONTRIBUTES TO A SHOPPING LIST, and how many it feeds.
# Data: _data/food/aisles.yml, _data/food/servings.yml
# =============================================================================
# GitHub issue #801, Helen: "add scaler and shopping list feature to food
# recipe shortlist page ... no need to cost the portions ... When serving size
# is unclear, please make your best guess ... Group the shopping list by
# grocery aisle." The cocktails index has had the same feature since #546; this
# is food's half, and the parts that differ are the two she named.
#
# WHY A BUILD-TIME PLUGIN AND NOT LIQUID, the same argument
# _plugins/cocktail_costs.rb makes. Assigning an aisle means finding the
# LONGEST keyword that appears as a whole word in a free-text ingredient name,
# across a table of some 400 keywords, once for each of 778 ingredients. Liquid
# can express that only as a nested loop per ingredient inside a template that
# is already 584 lines, and it would re-run on every render. Ruby does it once.
#
# WHY THE ANSWER GOES INTO THE PAGE RATHER THAN THE TABLE. The browser is
# handed `{amount, name, aisle}` and never sees aisles.yml, so there is exactly
# one implementation of the matching rule and no chance of the page and the
# build disagreeing about where cream lives. It also means
# tests/test_rendered_pages.py can read the built index and check the aisle of
# every real ingredient in the collection, which is the only check that would
# have caught `garlic cloves` landing on the spice rack -- and it did.
#
# WHAT THIS DELIBERATELY DOES NOT DO: arithmetic. Every amount is passed
# through as the string the recipe wrote, because scaling and totalling belong
# to assets/js/shopping-list.js, which owns the ONE amount parser this codebase
# has (MANUAL 9.13) and is tested without a browser. A second parser in Ruby is
# the drift this file exists to avoid everywhere else.
#
# -----------------------------------------------------------------------------
# THE NAME IS TRUNCATED THE SAME WAY THE INDEX'S EXCLUSION VOCABULARY IS
# -----------------------------------------------------------------------------
# food/index.html derives `data-all-ingredients` by taking each item name up to
# its first comma or open bracket, so "butter beans, drained" indexes as
# "butter beans". A shopping list wants exactly that: "drained" is a
# preparation note and not a thing in a shop, and two recipes writing the same
# bean with different notes must total onto one line. The two derivations agree
# by construction rather than by comment --
# test_the_shopping_list_and_the_ingredient_index_agree_on_a_name reads both
# out of the built page and compares them.
#
# THE ONE PLACE THEY DIVERGE IS A CROSS-RECIPE LINK, and deliberately. Issue
# #273 drops `item: "[grandma's lemon curd](../grandmas-lemon-curd/)"` from the
# exclusion index, because a pointer to another ingredient list is not a single
# food you can ask to avoid. It IS a line on a shopping list -- you have to
# have made the curd -- so this keeps it, prints the link's own text, and sends
# it to `other` outright rather than letting a keyword claim it. Five items
# across the collection are this shape.
#
# AN `incidental:` ITEM IS SKIPPED, which is the opposite of what the exclusion
# index does with one, and both are right. The flag marks a cooking fluid the
# recipe PAGE's Ingredients section already hides (MANUAL 4); the shopping list
# answers "what do I buy for this", so it hides it too. The exclusion filter
# answers "does this dish contain the thing I am avoiding", where "we didn't
# itemise the frying oil" is not an answer. Same flag, two questions, two
# answers -- and only one recipe carries it today.
# =============================================================================

module HelenTriages
  class FoodShopping < Jekyll::Generator
    safe true
    priority :normal

    COLLECTIONS = %w[food_recipes food_magic_bag food_drafts].freeze

    # A `serves:` counts as stated when it OPENS with a number. "4", "4–6" and
    # "4, generously" all do; "Depends on appetite" does not, and the low end
    # of a range is taken because over-buying is the safe direction for a
    # shopping list. Helen's own rule stands untouched either way: a `serves:`
    # value may be prose in her voice and is never tidied into a number
    # (MANUAL 4).
    LEADING_NUMBER = /\A\s*(\d+)/

    def generate(site)
      aisles = site.data.dig("food", "aisles")
      return unless aisles

      @order    = Array(aisles["order"]).map { |a| a["key"] }
      @never    = Array(aisles["never"]).map { |n| fold(n) }
      @guesses  = site.data.dig("food", "servings", "portions") || {}

      # LONGEST FIRST, AND THAT IS THE WHOLE MATCHING RULE. Sorted once here
      # rather than compared per lookup: `coconut milk` must be tried before
      # `milk`, `peanut butter` before `butter`, `garlic cloves` before
      # `cloves`. Ties break on the keyword itself only so the order is stable
      # between builds; no real pair depends on it.
      @keywords = []
      (aisles["keywords"] || {}).each do |aisle, words|
        Array(words).each { |w| @keywords << [fold(w), aisle] }
      end
      @keywords.sort_by! { |word, _| [-word.length, word] }

      # Compiled once. `(?<![a-z0-9])` rather than `\b` because a keyword may
      # end in a non-word character (`goat's cheese`), where `\b` asks about
      # the wrong side of the apostrophe.
      @patterns = @keywords.map do |word, aisle|
        [/(?<![a-z0-9])#{Regexp.escape(word)}(?![a-z0-9])/, aisle]
      end

      counted = 0
      guessed = 0
      COLLECTIONS.each do |key|
        next unless site.collections[key]
        site.collections[key].docs.each do |doc|
          portions, estimated = portions_for(doc)
          doc.data["portions"] = portions
          doc.data["portions_estimated"] = estimated
          doc.data["shopping"] = shopping_for(doc)
          counted += 1
          guessed += 1 if estimated
        end
      end

      Jekyll.logger.info "Shopping:", "read #{counted} food recipes " \
        "(#{guessed} portion counts guessed from _data/food/servings.yml)"
    end

    private

    # Lowercased, curly apostrophe flattened, whitespace collapsed. The same
    # fold assets/js/shopping-list.js applies, and for the same reason: it is
    # the KEY and never the label, so nothing here is ever shown to anybody.
    def fold(text)
      text.to_s.gsub("’", "'").strip.downcase.gsub(/\s+/, " ")
    end

    # [portions, estimated]. `nil` portions is a recipe nobody has given a
    # figure -- the page then simply offers no scaling for it, and
    # test_every_food_recipe_resolves_to_a_portion_count fails loudly, which is
    # the right way round: a missing guess must not stop a build.
    def portions_for(doc)
      stated = doc.data["serves"].to_s[LEADING_NUMBER, 1]
      return [stated.to_i, false] if stated

      slug = File.basename(doc.relative_path.to_s, ".*")
      guess = @guesses[slug]
      return [guess.to_i, true] if guess.is_a?(Numeric) && guess.to_i > 0

      [nil, false]
    end

    # Both shapes, in one pass. A recipe has `ingredient_groups` and no
    # `ingredients`; a magic-bag entry has `ingredients` and no
    # `ingredient_groups` (MANUAL 4.3), so each loop is a no-op for the other
    # and neither needs a branch on the collection. A magic-bag item carries no
    # amount at all, which is not a gap to fill: the shopping list counts an
    # unquantified entry rather than summing it, exactly as it does for a
    # cocktail's `to top`.
    def shopping_for(doc)
      items = []
      Array(doc.data["ingredient_groups"]).each do |group|
        items.concat(Array(group["items"]))
      end
      items.concat(Array(doc.data["ingredients"]))

      rows = []
      items.each do |item|
        if item.is_a?(Hash)
          next if item["incidental"]
          raw = item["item"]
          amount = item["amount"]
        else
          raw = item
          amount = nil
        end
        next if raw.nil? || raw.to_s.strip.empty?

        name, aisle = name_and_aisle(raw.to_s)
        next if name.nil?

        rows << { "amount" => amount.to_s, "name" => name, "aisle" => aisle }
      end
      rows
    end

    # A cross-recipe link, or an ordinary name truncated at its first comma or
    # open bracket. See the header for why the two are treated differently.
    LINK = /\A\[([^\]]+)\]\(/

    def name_and_aisle(raw)
      text = raw.strip

      if (link = text[LINK, 1])
        return [link.strip, "other"]
      end

      name = text.split(/[,(]/).first.to_s.strip
      return [nil, nil] if name.empty?

      key = fold(name)
      return [nil, nil] if @never.include?(key)

      [name, aisle_for(key)]
    end

    def aisle_for(key)
      @patterns.each do |pattern, aisle|
        return aisle if pattern.match?(key)
      end
      "other"
    end
  end
end
