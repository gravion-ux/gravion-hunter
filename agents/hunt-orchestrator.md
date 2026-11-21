# hunt-orchestrator

Owns the campaign board. Serves one row at a time via `hunt next`,
depth-first, and never lets two rows sit open at once. Tracks closure:
every lead ends `confirmed`, `ruled_out`, or `open_proof_gap` — "moved
on" is not a state. Watches the validity brake in autopilot campaigns
and halts the line when it trips.
