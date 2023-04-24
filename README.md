# Huq's Sqlfluff Plugin

A [sqlfluff](https://github.com/sqlfluff/sqlfluff) plugin for Huq to enforce our heavily opinionated rules for more consistentcy that sqlfluff can bring out of the box.

## How to develop this?

1. Assume you have a venv enabled
2. `pip install -e .`
3. Hack.
4. Make sure you add sensible tests and the tests pass.

## How to test this?

```bash
pytest
```

The test cases are in [test/rules/test_cases/](test/rules/test_cases/).
