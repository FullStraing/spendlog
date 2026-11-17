# spendlog — tiny CLI expense tracker

A no-dependency Python CLI for tracking spending when the budget is tight.
One JSON file (`spendlog.json`) holds expenses and monthly budgets — nothing
leaves your machine.

## Why

Knowing where the money goes beats guessing. Log each purchase in seconds
and see, per month, what each category cost against the budget you set.

## Usage

```bash
python spendlog.py add 4.50 coffee "oat latte"
python spendlog.py add 12.00 groceries
python spendlog.py list
python spendlog.py list --category coffee
python spendlog.py month            # this month, totals by category
python spendlog.py month 2026-10   # a specific month
python spendlog.py budget food 200  # $200/month budget for food
python spendlog.py budgets          # spending vs. budget, this month
```

Example output:

```
$ python spendlog.py month
coffee          $   32.50
food            $  148.20
TOTAL           $  180.70
budget food: $148.20 / $200.00 ($51.80 left)
```

## Notes

- Amounts must be positive; categories are lower-cased and trimmed.
- Dates default to today; pass `--date YYYY-MM-DD` to backdate.
- Set `SPENDLOG_FILE` to store data somewhere else.
- Expenses are never deleted by the tool — edit `spendlog.json` by hand if
  you logged something wrong.

## Tests

```bash
python -m unittest -v
```
