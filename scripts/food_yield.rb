# frozen_string_literal: true

# Read `makes:` lines the way the build does, without building the site.
#
#   ruby scripts/food_yield.rb "4–6 waffles, depending on your waffle iron" "950 ml"
#
# Prints one JSON object: each argument as a key, and what
# _plugins/food_yield.rb makes of it as the value (null where the line does not
# open with a count of something named, which keeps the portions box). The
# vocabulary is the real one, `yields:` in _data/food/scaling.yml.
#
# WHY IT EXISTS: the parser is a Jekyll plugin's helper, and the only other
# way to ask it a question is a full build. tests/test_food_yield.py runs this
# once over every shape the two collections write (#1286).
#
# Arguments are `makes:` texts and nothing else. It reads two files in this
# repository and writes nothing.

require "json"
require "yaml"

root = File.expand_path("..", __dir__)
require File.join(root, "_plugins", "food_yield.rb")

vocab = YAML.safe_load(
  File.read(File.join(root, "_data", "food", "scaling.yml"), encoding: "utf-8")
)["yields"]

out = {}
ARGV.each do |text|
  text = text.dup.force_encoding("utf-8")
  out[text] = HelenTriages::FoodYield.parse(text, vocab)
end
puts JSON.generate(out)
