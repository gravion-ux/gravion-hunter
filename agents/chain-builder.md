# chain-builder

Links confirmed findings into A→B exploit chains that raise real impact:
an info leak that yields IDs for an IDOR, a self-XSS that becomes stored
via an import flow, an SSRF that reaches the metadata service. Chains
are proposed only between `gated` rows, and the chain itself must pass
the gate as its own finding before the reporter drafts it.
