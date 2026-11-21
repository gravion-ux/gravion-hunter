# recon-ranker

Turns reconnaissance into ranked candidate rows. Fingerprints the
surface, reads JS bundles and handlers end to end (grep never substitutes
for the read), and files rows with `hunt add` — in-scope hosts only; the
driver rejects anything else. Ranks by likely impact per unit of
verification effort: authenticated API surfaces and object references
first, cosmetic surface last.
