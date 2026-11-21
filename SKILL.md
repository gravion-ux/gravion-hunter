---
name: gravion-hunter
description: Autonomous bug bounty campaign driver with enforced scope, a hard 7-question validation gate, dedupe-in-the-loop, and a validity brake on autopilot submission. Use when starting or resuming a bug bounty engagement on an authorised programme.
---

# gravion-hunter — master skill

The driver is the plan. Run `hunt next`, do what it serves, record the
result, repeat. The gates live in the state machine, not in your memory —
a finding physically cannot reach `reported` without passing the gate and
the dedupe transition.

## Start / resume

1. Write `scope.md` from the programme brief (in-scope and out-of-scope
   hosts). An empty scope is the one thing the framework cannot invent.
2. `hunt init --scope scope.md --state campaign.json`
   Add `--autopilot` only when the operator has explicitly opted into
   autonomous submission for this campaign.
3. Recon feeds rows via `hunt add` — out-of-scope hosts are rejected by
   the driver, not by your discipline.
4. Loop: `hunt next` → work the row → `hunt close` with exactly one of
   `confirmed` / `ruled_out` / `open_proof_gap`.

## After a confirmed finding

```
hunt gate   --row N --answers all          # or name the failure with --fail
hunt dedupe --row N --sources a,b,c        # minimum 3 recorded sources
hunt report --row N
hunt submit --row N --approve              # approval mode
hunt outcome --row N --result valid        # feed the brake
```

## Rules that outrank everything else

- Scope is law. If the driver rejects a host, the host is not tested.
- One failed gate question kills the finding. Record why, move on.
- Dedupe happens BEFORE drafting, never after.
- Reports claim only proven impact. The phrase "could potentially" is a
  defect; fix it or kill the claim.
- In autopilot, watch the brake: if it trips, stop and review the last
  outcomes before resuming. The brake exists because a damaged validity
  ratio costs more than any single bounty pays.
