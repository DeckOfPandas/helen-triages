# What a food recipe contributes to a shopping list, and how many it feeds
# (#801). Data: _data/food/aisles.yml and each recipe's `serves:`/`makes:`.
#
# The browser is handed `{amount, name, aisle}` and never sees aisles.yml, so
# there is one implementation of the matching rule. No arithmetic here: every
# amount is passed through as written and the scripts in assets/js/ do the sums.
# The name is cut at its first comma or open bracket, exactly as food/index.html
# derives `data-all-ingredients`, so two recipes writing one bean with different
# notes total onto one line
# (test_the_shopping_list_and_the_ingredient_index_agree_on_a_name).
# A cross-recipe link (`[grandma's lemon curd](../...)`) is kept, shown as its
# link text and filed under `other`; #273 drops it from the exclusion index.
# An `incidental:` item is skipped: the list answers "what do I buy".

module HelenTriages
  class FoodShopping < Jekyll::Generator
    safe true
    priority :normal

    COLLECTIONS = %w[food_recipes food_magic_bag food_drafts].freeze

    # A `serves:` counts as stated when it opens with a number: "4", "4–6" and
    # "4, generously" do; "Depends on appetite" does not. The low end of a range
    # is taken: under-catering is worse than over-catering, and the smaller base
    # gives the bigger multiplier. A `serves:` value may be prose and is never
    # tidied into a number.
    LEADING_NUMBER = /\A\s*(\d+)/

    def generate(site)
      aisles = site.data.dig("food", "aisles")
      return unless aisles

      @order    = Array(aisles["order"]).map { |a| a["key"] }
      @never    = Array(aisles["never"]).map { |n| fold(n) }

      # Longest first, which is the whole matching rule: `coconut milk` before
      # `milk`, `garlic cloves` before `cloves`. Ties break on the keyword only
      # to keep the order stable between builds.
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
      COLLECTIONS.each do |key|
        next unless site.collections[key]
        site.collections[key].docs.each do |doc|
          doc.data["made"] = made_for(doc, yields)
          portions = portions_for(doc)
          doc.data["portions"] = portions
          doc.data["whole_recipes"] = whole_recipes?(doc)
          doc.data["half_recipe"] = doc.data["whole_recipes"] &&
            HelenTriages::HalfRecipe.judge(
              doc.data["ingredient_groups"], doc.data["made"], portions,
              site.data.dig("food", "scaling", "half_recipe"),
              site.data.dig("food", "scaling", "half_step_measures")
            )["ok"]
          doc.data["shopping"] = shopping_for(doc)
          counted += 1
        end
      end

      Jekyll.logger.info "Shopping:", "read #{counted} food recipes"
    end

    private

    # Lowercased, curly apostrophe flattened, whitespace collapsed. A key, never
    # a label.
    def fold(text)
      text.to_s.gsub("’", "'").strip.downcase.gsub(/\s+/, " ")
    end

    # How many it feeds (#815): the number opening `serves:`, or nil. A
    # `makes:` recipe is counted by `made_for` instead, never as people. A
    # recipe with neither gets no scaler, which tests/test_food_shopping.py
    # allows only on a draft whose yield is still `QQ`.
    def portions_for(doc)
      stated = doc.data["serves"].to_s[LEADING_NUMBER, 1]
      stated ? stated.to_i : nil
    end

    # What the recipe makes, for the recipe page's scaler (#1286): `page.made` is
    # FoodYield.parse's reading of `makes:`, or nil. Where it is set the page's
    # box counts the thing made and never prints "portions". Not `makes:` read as
    # people: `page.portions` is still how many it feeds. A recipe that states
    # `serves:` never gets one.
    def made_for(doc, yields)
      return nil if doc.data["serves"].to_s[LEADING_NUMBER, 1]
      makes = doc.data["makes"]
      return nil if makes.nil? || makes.to_s.strip.empty?
      HelenTriages::FoodYield.parse(makes.to_s, yields)
    end

    # A `makes:` recipe is scaled in whole recipes (#1286), including one whose
    # yield `made_for` cannot read and which keeps the portions box. A recipe
    # that states `serves:` scales a portion at a time (#1005).
    def whole_recipes?(doc)
      return false if doc.data["serves"].to_s[LEADING_NUMBER, 1]
      !doc.data["makes"].to_s.strip.empty?
    end

    # Both shapes in one pass: a recipe has `ingredient_groups`, a magic-bag
    # entry has `ingredients`. A magic-bag item carries no amount; the list
    # counts it unquantified.
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

    # Marks which part of which whole fruit a line uses (#1297), so
    # assets/js/food-shopping-list.js can merge "zest of 1 lemon" and "juice of 1
    # lemon" into one lemon. Vocabulary: `whole_fruit:` in _data/food/scaling.yml.
    # `name` is never changed, because the exclusion index must agree on it.
    #   "parts"   => ["juice", "zest"]   the parts this line uses
    #   "fruit"   => "lemon"             only where the count is in the item
    #   "count"   => "1"                 the amount read out of the item
    #   "pointer" => true                buys nothing: "the rest of the oil above"
    def mark_fruit(row, raw)
      vocab = @fruit
      return if vocab.nil?
      head, note = raw.strip.split(/[,(]/, 2)
      # A bracket after the note is an aside, not the part: "lemons, juiced
      # (use the ones you've zested)" is juice only.
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
    # and then no row is marked.
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
        # The fruit is the last word of the name: "unwaxed lemons", not "lemon juice".
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
