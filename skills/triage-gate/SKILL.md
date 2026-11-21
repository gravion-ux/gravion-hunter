---
name: triage-gate
description: The 7-Question Gate — validation before any report is drafted. One wrong answer kills the finding.
---

# Triage gate

Ask in order. One wrong answer = STOP, record the failure, move on.
"N/A hurts your validity ratio. Informative is neutral. Only submit what
passes all 7 questions."

1. **Exploitable now?** Write the setup, the exact copy-paste HTTP
   request, the result, the real-world impact, and the cost. If the
   request cannot be written, there is no finding.
2. **Accepted impact?** Map the bug to the programme's vulnerability
   types and out-of-scope list. An exclusion mapping kills it here.
3. **In-scope asset?** Production and listed — not staging, not a
   third-party service the company merely uses.
4. **No privileged shortcut?** "Admin can do X" is not a bug.
   "Non-admin can do what only admin should" is.
5. **Not known behaviour?** Disclosed reports, changelogs, issues and
   public write-ups searched (the dedupe-checker owns the deep pass).
6. **Impact proven?** XSS shows session impact, not `alert(1)`; SSRF
   returns internal data, not a DNS ping; SQLi exfiltrates real rows;
   IDOR returns another user's actual data, not a 200. "Technically
   possible" only = downgrade, not death.
7. **Not an invalid class?** If the class is on the programme's
   never-submit list and stands unchained, it dies here.

The driver stores the seven answers on the row; `gated` is unreachable
until all seven are recorded true.
