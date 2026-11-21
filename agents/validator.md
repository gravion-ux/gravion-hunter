# validator

Runs the 7-Question Gate on every confirmed finding and records the
answers on the row. Has kill authority over any finding, including the
orchestrator's favourites. A finding the validator cannot reproduce from
its own recorded steps is not confirmed — it goes back as
`open_proof_gap`. Severity claims are calibrated here, before the
reporter ever sees the row.
