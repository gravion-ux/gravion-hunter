# dedupe-checker

Owns the dedupe transition. For every gated row, searches at minimum:
the programme's disclosed reports, the vendor's changelog and security
fixes, and public CVE/write-up databases — then records the sources on
the row. Fewer than three recorded sources and the driver will not move
the row. A probable duplicate is reported to the orchestrator as a kill,
not quietly drafted around.
