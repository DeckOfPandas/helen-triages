# =============================================================================
# WHAT A FOOD RECIPE CONTRIBUTES TO A SHOPPING LIST, and how many it feeds.
# Data: _data/food/aisles.yml, and each recipe's own `serves_estimate:`
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
    # of a range is taken because Helen ruled it so on 2026-09-07, and gave
    # the reason: "when it's a range, pick the lower number because
    # under-catering is worse for me than over-catering". The arithmetic runs
    # the way that sounds backwards until you do it -- the scale is portions
    # wanted OVER portions made, so the SMALLER base gives the BIGGER
    # multiplier and more food. The same rule governs a `serves_estimate:`
    # written from a range. Over-buying is the safe direction for a
    # shopping list. Helen's own rule stands untouched either way: a `serves:`
    # value may be prose in her voice and is never tidied into a number
    # (MANUAL 4).
    LEADING_NUMBER = /\A\s*(\d+)/

    def generate(site)
      aisles = site.data.dig("food", "aisles")
      return unless aisles

      @order    = Array(aisles["order"]).map { |a| a["key"] }
      @never    = Array(aisles["never"]).map { |n| fold(n) }

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

      yields = site.data.dig("food", "scaling", "yields")
      @fruit = fruit_vocabulary(site.data.dig("food", "scaling", "whole_fruit"))

      counted = 0
      guessed = 0
      COLLECTIONS.each do |key|
        next unless site.collections[key]
        site.collections[key].docs.each do |doc|
          portions, estimated = portions_for(doc)
          doc.data["portions"] = portions
          doc.data["portions_estimated"] = estimated
          doc.data["made"] = made_for(doc, yields)
          doc.data["whole_recipes"] = whole_recipes?(doc)
          doc.data["half_recipe"] = doc.data["whole_recipes"] &&
            HelenTriages::HalfRecipe.judge(
              doc.data["ingredient_groups"], doc.data["made"], portions,
              site.data.dig("food", "scaling", "half_recipe"),
              site.data.dig("food", "scaling", "half_step_measures")
            )["ok"]
          doc.data["shopping"] = shopping_for(doc)
          counted += 1
          guessed += 1 if estimated
        end
      end

      Jekyll.logger.info "Shopping:", "read #{counted} food recipes " \
        "(#{guessed} portion counts from serves_estimate:)"
    end

    private

    # Lowercased, curly apostrophe flattened, whitespace collapsed. The same
    # fold assets/js/shopping-list.js applies, and for the same reason: it is
    # the KEY and never the label, so nothing here is ever shown to anybody.
    def fold(text)
      text.to_s.gsub("’", "'").strip.downcase.gsub(/\s+/, " ")
    end

    # [portions, estimated]. Two sources and one order, #815.
    #
    # `serves:` FIRST, because a number Helen wrote beats a number anyone
    # estimated. `serves_estimate:` second, and everything from there is
    # flagged so the page can print its `~`.
    #
    # `makes:` IS NEVER READ AS PEOPLE, however numeric it looks: 950 ml is not
    # 950 portions and "12 slices" is not necessarily twelve people. That is
    # the whole reason `serves_estimate` exists as its own key rather than the
    # plugin being cleverer about `makes:`.
    #
    # `nil` is still possible -- a recipe carrying neither -- and the page then
    # offers no scaling for it while
    # test_every_food_recipe_states_how_many_it_feeds fails loudly. A missing
    # figure must not stop a build; it must stop a test.
    def portions_for(doc)
      stated = doc.data["serves"].to_s[LEADING_NUMBER, 1]
      return [stated.to_i, false] if stated

      estimate = doc.data["serves_estimate"]
      return [estimate.to_i, true] if estimate.is_a?(Numeric) && estimate.to_i > 0

      [nil, false]
    end

    # WHAT THE RECIPE MAKES, FOR THE RECIPE PAGE'S SCALER -- #1286. `page.made`
    # is _plugins/food_yield.rb's reading of `makes:`: a count of a named
    # thing ("4–6 waffles"), a measure ("950 ml"), or nil. Helen: "Never tell
    # me how many cookies are in a portion!!!" -- so where this is set, the
    # recipe page's box counts the thing made and the word "portions" is not
    # printed.
    #
    # THIS IS NOT `makes:` BEING READ AS PEOPLE. `portions_for` above is
    # unchanged and still refuses to; `page.portions` is still the
    # `serves_estimate`. Two figures, two questions: how many it feeds, and
    # how many it makes. (The INDEX's shopping list scaled these recipes by
    # the first until #1297; it counts batches from the second now.)
    #
    # A recipe that states `serves:` never gets one, whatever else it says:
    # a number Helen wrote about people wins. No file carries both today.
    def made_for(doc, yields)
      return nil if doc.data["serves"].to_s[LEADING_NUMBER, 1]
      makes = doc.data["makes"]
      return nil if makes.nil? || makes.to_s.strip.empty?
      HelenTriages::FoodYield.parse(makes.to_s, yields)
    end

    # A `makes:` RECIPE IS SCALED IN WHOLE RECIPES, whatever its box counts --
    # #1286. Helen: "the buttons should still multiply the recipe in integers",
    # and, for a yield with no number to show: 'if "some" is originally guessed
    # to be 4 portions, 2x should be 8 portions'. So this is true for every
    # recipe whose yield is `makes:`, including the ones `made_for` cannot read
    # and which therefore keep the portions box. A recipe that states `serves:`
    # is scaled a portion at a time, as it always was (#1005).
    def whole_recipes?(doc)
      return false if doc.data["serves"].to_s[LEADING_NUMBER, 1]
      !doc.data["makes"].to_s.strip.empty?
    end

    # ONE STEP BELOW A WHOLE RECIPE, x½, WHERE THE NUMBERS ARE NOT INSANE --
    # Helen's phrase. `page.half_recipe` is _plugins/food_half_recipe.rb's
    # verdict, and that file has the rule. Only ever asked of a recipe that
    # steps in whole recipes; a `serves:` recipe already goes down a portion
    # at a time.

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

        row = { "amount" => amount.to_s, "name" => name, "aisle" => aisle }
        mark_fruit(row, raw.to_s) unless raw.to_s.strip.match?(LINK)
        rows << row
      end
      rows
    end

    # ONE FRUIT, TWO PARTS, AND A LINE THAT ONLY POINTS -- #1297. Helen,
    # 2026-10-09: 'I would like to cleverly combine e.g. "zest of 1 lemon" and
    # "juice of 1 lemon" to make "1 lemon" in the shopping list.'
    #
    # THIS ONLY MARKS THE ROW. The merging is arithmetic and belongs to
    # assets/js/food-shopping-list.js, like every other sum; what it needs
    # from here is which part of which fruit a line uses. The vocabulary is
    # `whole_fruit:` in _data/food/scaling.yml, and its header has the rule.
    #
    # `name` IS NEVER CHANGED, because the exclusion index and this list must
    # agree on it (test_the_shopping_list_and_the_ingredient_index_agree_on_a
    # _name). "juice of 1 lemon" keeps that name and gains `fruit` and `count`
    # beside it, which is what the list groups and totals by instead.
    #
    #   "parts"   => ["juice", "zest"]   the parts this line uses
    #   "fruit"   => "lemon"             only where the count is in the item
    #   "count"   => "1"                 the amount read out of the item
    #   "pointer" => true                buys nothing: "the rest of the oil above"
    def mark_fruit(row, raw)
      vocab = @fruit
      return if vocab.nil?
      head, note = raw.strip.split(/[,(]/, 2)
      # A BRACKET AFTER THE NOTE IS AN ASIDE, NOT THE PART. "lemons, juiced
      # (use the ones you've zested)" is juice: read as zest too, it added
      # two lemons to a cake that had already zested four.
      note = note.to_s.split("(", 2).first if raw.strip[head.to_s.length] == ","
      head = fold(head)
      note = fold(note)
      unstated = row["amount"].strip.empty?

      if unstated && (vocab[:pointer].match?(note) || vocab[:pointer].match?(head))
        row["pointer"] = true
        return
      end

      if unstated && (m = vocab[:literal].match(head))
        count = m[:count]
        count = "1" if %w[a an one].include?(count)
        count = "½" if count == "half"
        size = m[:size].to_s.strip
        # As written, plural and all: "juice of 2 limes" is "2 limes".
        row["fruit"] = "#{m[:fruit]}#{m[:plural]}"
        row["count"] = size.empty? || size == "juicy" || size == "unwaxed" ? count : "#{count} #{size}"
        row["parts"] = [m[:first], m[:second]].compact.map { |w| vocab[:part_of][w] }.uniq
        row["aisle"] = aisle_for(m[:fruit])
        return
      end

      return unless vocab[:named].match?(head)
      parts = note.scan(vocab[:part_word]).flatten.map { |w| vocab[:part_of][w] }.uniq
      row["parts"] = parts unless parts.empty?
    end

    # Compiled once per build from `whole_fruit:`; nil when the data is absent,
    # and then no row is marked and the list totals as it did before #1297.
    def fruit_vocabulary(data)
      return nil unless data.is_a?(Hash)
      fruits = Array(data["fruits"]).map { |w| fold(w) }.reject(&:empty?)
      part_of = {}
      (data["parts"] || {}).each do |part, words|
        Array(words).each { |w| part_of[fold(w)] = part.to_s }
      end
      return nil if fruits.empty? || part_of.empty?

      any = ->(words) { words.sort_by { |w| -w.length }.map { |w| Regexp.escape(w) }.join("|") }
      fruit = any.call(fruits)
      part = any.call(part_of.keys)
      preps = any.call(Array(data["preparations"]).map { |w| fold(w) })
      sizes = any.call(Array(data["sizes"]).map { |w| fold(w) })
      pointers = any.call(Array(data["pointers"]).map { |w| fold(w) })
      count = '\d+(?:\.\d+)?(?:\s*[½¼¾⅓⅔])?|[½¼¾⅓⅔]|an?|one|half'

      {
        part_of: part_of,
        part_word: /(?<![a-z])(#{part})(?![a-z])/,
        # The fruit is the LAST word of the name: "unwaxed lemons", not "lemon juice".
        named: /(?<![a-z])(?:#{fruit})s?\z/,
        literal: /\A(?:(?:#{preps})\s+)*(?<first>#{part})(?:\s+and\s+(?<second>#{part}))?\s+(?:of\s+)?(?<count>#{count})\s+(?:an?\s+)?(?<size>(?:(?:#{sizes})\s+)*)(?<fruit>#{fruit})(?<plural>s)?\z/,
        pointer: /\A(?:(?:#{pointers})(?![a-z])|the\s+(?:#{part})\s+of\s+the\s+ones?(?![a-z]))/
      }
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
