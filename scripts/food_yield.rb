# frozen_string_literal: true

# Ask the build's two yield readers a question, without building the site.
#
#   ruby scripts/food_yield.rb "4–6 waffles, depending on your waffle iron" "950 ml"
#
# Prints one JSON object: each argument as a key, and what
# _plugins/food_yield.rb makes of it as the value (null where the line does not
# open with a count of something named, which keeps the portions box).
#
#   ruby scripts/food_yield.rb --half tmp/recipes.json
#
# Reads a JSON list of {"key", "makes", "serves", "serves_estimate",
# "ingredient_groups"} and prints, per key, the reading of `makes:` and
# _plugins/food_half_recipe.rb's verdict on whether the recipe is offered a
# half step: {"made": ..., "half": {"ok": true/false, "why": "..."}}. The
# same three steps _plugins/food_shopping.rb takes for a real recipe.
#
# The vocabulary is the real one, _data/food/scaling.yml.
#
# WHY IT EXISTS: both readers are a Jekyll plugin's helpers, and the only
# other way to ask them anything is a full build. tests/test_food_yield.py
# runs this over every shape the two collections write (#1286).
#
# It reads files in this repository (plus the one JSON file named) and writes
# nothing.

require "json"
require "yaml"

root = File.expand_path("..", __dir__)
require File.join(root, "_plugins", "food_yield.rb")
require File.join(root, "_plugins", "food_half_recipe.rb")

scaling = YAML.safe_load(
  File.read(File.join(root, "_data", "food", "scaling.yml"), encoding: "utf-8")
)
vocab = scaling["yields"]

out = {}
if ARGV[0] == "--half"
  abort "usage: ruby scripts/food_yield.rb --half <file.json>" unless ARGV.length == 2
  JSON.parse(File.read(ARGV[1], encoding: "utf-8")).each do |recipe|
    stated = recipe["serves"].to_s[/\A\s*(\d+)/, 1]
    makes = recipe["makes"].to_s
    made = stated || makes.strip.empty? ? nil : HelenTriages::FoodYield.parse(makes, vocab)
    estimate = recipe["serves_estimate"]
    portions = stated ? stated.to_i : (estimate.is_a?(Numeric) ? estimate.to_i : nil)
    out[recipe["key"]] = {
      "made" => made,
      "half" => HelenTriages::HalfRecipe.judge(
        recipe["ingredient_groups"], made, portions,
        scaling["half_recipe"], scaling["half_step_measures"]
      )
    }
  end
else
  ARGV.each do |text|
    text = text.dup.force_encoding("utf-8")
    out[text] = HelenTriages::FoodYield.parse(text, vocab)
  end
end
puts JSON.generate(out)
