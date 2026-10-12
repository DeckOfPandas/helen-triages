# Run _plugins/amount.rb over a list of amount strings and print what it read.
#
#     ruby scripts/parse_amounts.rb tests/fixtures/amounts.json
#
# The argument is a JSON file holding either a list of strings or a list of
# objects with an `amount` key (the fixture's own shape). Prints a JSON list of
# {"amount", "number", "unit", "ml"}: `number` is null for an amount with no
# figure, `ml` is null for one that is not a volume.
#
# It gives the Ruby parser a test that does not cost a Jekyll build (#1199):
# tests/test_amount_parser.py shells out to it. A file, not `ruby -e`, because
# .claude/hooks/guard-inline-script.py refuses an inline program.
#
# Reads only: the file named, and _data/cocktails/ingredients.yml for the
# ignored words and the millilitre table the plugins themselves use.
require "json"
require "yaml"
require_relative "../_plugins/amount"

path = ARGV[0] or abort "usage: ruby scripts/parse_amounts.rb <amounts.json>"
root = File.expand_path("..", __dir__)
measures = YAML.safe_load(
  File.read(File.join(root, "_data", "cocktails", "ingredients.yml"))
)["measures"]
ignored = measures["ignored_words"] || []
per_ml = measures["per_ml"]

rows = JSON.parse(File.read(path)).map do |row|
  amount = row.is_a?(Hash) ? row["amount"] : row
  number, unit = HelenTriages::Amount.parse(amount, ignored)
  {
    "amount" => amount,
    "number" => number,
    "unit"   => unit,
    "ml"     => HelenTriages::Amount.millilitres(amount, per_ml, ignored)
  }
end
puts JSON.pretty_generate(rows)
