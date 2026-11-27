"""Scope parsing and enforcement.

A campaign cannot exist without a scope file, and no row may be added for an
out-of-scope host. The scope file is a small markdown document:

    # Programme scope
    ## In scope
    - example.com
    - *.example.com
    - api.example.net
    ## Out of scope
    - staging.example.com
    - login.example.com

Out-of-scope always wins over in-scope. Wildcards match one or more labels
below the base domain (``*.example.com`` matches ``a.example.com`` and
``a.b.example.com`` but not ``example.com`` itself).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


class ScopeError(ValueError):
    """Raised when a scope file is malformed or a host is out of scope."""


def _host_of(value: str) -> str:
    value = value.strip().lower()
    if "://" in value:
        host = urlparse(value).hostname or ""
        return host.lower()
    # Strip any path/port the operator may have left in.
    return value.split("/")[0].split(":")[0]


def _normalize_entry(entry: str) -> str:
    """Normalise a scope entry to a host or ``*.host`` pattern.

    Operators often paste URLs or ``host:port/path`` forms; storing those
    verbatim would make the entry never match a parsed host.
    """
    value = entry.strip().lower()
    if value.startswith("*."):
        return "*." + _host_of(value[2:])
    return _host_of(value)


def _matches(pattern: str, host: str) -> bool:
    pattern = pattern.strip().lower()
    if pattern.startswith("*."):
        base = pattern[2:]
        return host != base and host.endswith("." + base)
    return host == pattern


@dataclass
class Scope:
    in_scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    program: str = ""

    @classmethod
    def from_text(cls, text: str) -> "Scope":
        scope = cls()
        section: str | None = None
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("#"):
                heading = line.lstrip("#").strip().lower()
                if "out of scope" in heading or "out-of-scope" in heading:
                    section = "out"
                elif "in scope" in heading or "in-scope" in heading:
                    section = "in"
                elif scope.program == "" and line.startswith("# "):
                    scope.program = line[2:].strip()
                continue
            if section and line.startswith(("-", "*")):
                entry = line[1:].strip().strip("`")
                if entry:
                    target = scope.in_scope if section == "in" else scope.out_of_scope
                    normalized = _normalize_entry(entry)
                    if normalized and normalized not in target:
                        target.append(normalized)
        if not scope.in_scope:
            raise ScopeError("scope file declares no in-scope hosts; refusing to hunt blind")
        return scope

    @classmethod
    def from_file(cls, path: str) -> "Scope":
        with open(path, encoding="utf-8") as fh:
            return cls.from_text(fh.read())

    def check(self, host_or_url: str) -> bool:
        """True when the host is in scope. Out-of-scope entries win."""
        host = _host_of(host_or_url)
        if not host:
            return False
        if any(_matches(p, host) for p in self.out_of_scope):
            return False
        return any(_matches(p, host) for p in self.in_scope)

    def require(self, host_or_url: str) -> str:
        host = _host_of(host_or_url)
        if not self.check(host):
            raise ScopeError(f"{host!r} is out of scope for this campaign")
        return host
