---
name: hunt-workflow
description: The campaign loop — recon to rows, one row at a time, honest closure for every lead.
---

# Hunt workflow

1. **Scope first.** No scope file, no campaign. Transcribe the programme
   brief into `scope.md` exactly; when in doubt, an asset is out.
2. **Recon feeds the board.** Every observation becomes a row via
   `hunt add` (host, class, endpoint). The driver rejects out-of-scope
   hosts — that rejection is final.
3. **One open row at a time, depth-first.** `hunt next` serves the row;
   finish it before opening another.
4. **Close honestly.** Every worked row ends as `confirmed`, `ruled_out`
   (name the specific control, at a specific location, that makes it
   safe), or `open_proof_gap` (plausible, unproven — logged, not dropped).
5. **Confirmed rows go to the validator**, then the dedupe-checker, then
   the reporter. No step is skippable; the state machine enforces the
   order.
6. **Record every outcome.** Programme verdicts feed the validity brake
   and the campaign's memory of what this programme accepts.
