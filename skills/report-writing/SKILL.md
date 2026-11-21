---
name: report-writing
description: Impact-first report writing for HackerOne/Bugcrowd-style programmes. Prove it or don't report it.
---

# Report writing

Impact-first. Human tone. No theoretical language. Triagers are people.

## The rule

Never write "could potentially", "could be used to", or "may allow".
Either it does the thing — proved — or the claim comes out.

- BAD: "This vulnerability could potentially allow an attacker to access user data."
- GOOD: "An attacker can read any user's order history by changing the
  `user_id` parameter. Confirmed with two test accounts: attacker (ID
  123) retrieved victim (ID 456) orders, including shipping address and
  payment-method last four digits."

## Structure

1. **Title** — [Class] in [endpoint] allows [actor] to [impact].
2. **Summary** — two sentences: what, and why it matters to this business.
3. **Steps to reproduce** — numbered, copy-paste requests, test-account
   roles named. Ship a runnable reproduction (curl script) with the
   evidence whenever the target allows it.
4. **Impact** — the proved consequence, with the evidence inline.
5. **Severity** — CVSS 3.1 vector + one sentence tying it to the impact.
6. **Remediation** — the specific control, at the specific location.

## Persistence

Every report leaves a folder on disk: the draft, the gate answers, the
dedupe sources, and the evidence. If it isn't on disk, it didn't happen.
