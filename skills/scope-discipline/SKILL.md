---
name: scope-discipline
description: Scope is law — how scope files are written and why the driver, not the operator, enforces them.
---

# Scope discipline

A scope file the agent is merely *asked* to respect will eventually be
violated by a tired operator, a clever page, or a plausible redirect.
gravion-hunter parses the scope and enforces it in the driver: a row for
an out-of-scope host cannot be created at all.

## Writing scope.md

- Transcribe the programme brief verbatim: every in-scope host, every
  exclusion, wildcards exactly as the programme states them.
- When the brief is ambiguous, the asset is OUT until the programme
  clarifies. Ambiguity is not permission.
- Staging/dev hosts are out unless the brief explicitly lists them.
- Third-party services the company merely uses (payment processors,
  auth providers, CDNs) are out unless explicitly listed.
- Re-read the brief when the programme updates it; scope files go stale.

## During the hunt

- Redirects, subdomains and sibling services discovered mid-hunt are
  checked against the scope before any request is crafted.
- A tempting out-of-scope lead is logged as a note — never tested "just
  to check". One out-of-scope test can end a researcher's account.
