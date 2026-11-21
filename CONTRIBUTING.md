# Contributing to gravion-hunter

Contributions are welcome — especially new agent role cards, skill
playbooks for additional vulnerability classes, and programme-specific
scope-file examples.

## Ground rules

- The driver's hard rules are not negotiable: scope enforcement, the
  7-Question Gate, the dedupe minimum, and the validity brake exist to
  protect researcher accounts. PRs that weaken them will be closed.
- Every behavioural change to the driver needs tests. Run `pytest`
  before opening a PR.
- Keep agent cards and skills short and operational — instructions an
  agent can execute, not essays.
- Responsible use only: examples must target fictional or explicitly
  public-scope programmes.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest
pytest -q
```
