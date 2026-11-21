"""Campaign state machine — the deterministic driver.

Every finding moves through one pipeline, and the driver (not the operator's
mood) owns the transitions:

    queued -> working -> confirmed -> gated -> deduped -> reported -> submitted
                  \\-> ruled_out        (gate failure at any question -> killed)
                  \\-> open_proof_gap

Hard rules enforced here, not in documentation:

* A row can only be added for an in-scope host (Scope.require).
* ``gated`` requires all 7 Gate answers recorded True. One False kills the row.
* ``deduped`` requires at least MIN_DEDUPE_SOURCES recorded dedupe sources.
* ``submitted`` requires autopilot mode OR an explicit operator approval token.
* Autopilot carries a validity brake: once enough outcomes are known, if the
  N/A + duplicate share crosses the threshold, autopilot submission halts.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .scope import Scope

GATE_QUESTIONS = (
    "exploitable_now",        # Q1 step-by-step, real request
    "accepted_impact",        # Q2 on the programme's accepted list
    "in_scope_asset",         # Q3 root cause in an in-scope asset
    "no_privileged_access",   # Q4 no unrealistic privileged access required
    "not_known_behaviour",    # Q5 not already known / accepted behaviour
    "impact_proven",          # Q6 impact proven beyond "technically possible"
    "not_invalid_class",      # Q7 not a known-invalid class without a chain
)

MIN_DEDUPE_SOURCES = 3
BRAKE_MIN_OUTCOMES = 5
BRAKE_MAX_BAD_RATIO = 0.30

ROW_STATES = (
    "queued", "working", "open_proof_gap", "ruled_out", "confirmed",
    "gated", "deduped", "reported", "submitted", "killed",
)

OUTCOMES = ("valid", "informative", "duplicate", "na")


class CampaignError(RuntimeError):
    """Raised on any illegal transition or unmet hard rule."""


class ApprovalRequired(CampaignError):
    """Submission attempted without autopilot mode or an approval token."""


class BrakeEngaged(CampaignError):
    """The autopilot validity brake has halted automatic submission."""


@dataclass
class Row:
    id: int
    host: str
    vuln_class: str
    endpoint: str
    state: str = "queued"
    gate: dict = field(default_factory=dict)
    dedupe_sources: list = field(default_factory=list)
    outcome: str | None = None
    notes: list = field(default_factory=list)


@dataclass
class Campaign:
    scope: Scope
    autopilot: bool = False
    rows: list = field(default_factory=list)
    _next_id: int = 1

    # -- row lifecycle ----------------------------------------------------
    def add_row(self, host_or_url: str, vuln_class: str, endpoint: str) -> Row:
        host = self.scope.require(host_or_url)
        row = Row(id=self._next_id, host=host, vuln_class=vuln_class, endpoint=endpoint)
        self._next_id += 1
        self.rows.append(row)
        return row

    def get(self, row_id: int) -> Row:
        for row in self.rows:
            if row.id == row_id:
                return row
        raise CampaignError(f"no row with id {row_id}")

    def _move(self, row: Row, expected: str, new_state: str) -> Row:
        if row.state != expected:
            raise CampaignError(
                f"row {row.id} is {row.state!r}; expected {expected!r} before -> {new_state!r}"
            )
        row.state = new_state
        return row

    def start(self, row_id: int) -> Row:
        return self._move(self.get(row_id), "queued", "working")

    def close(self, row_id: int, outcome: str) -> Row:
        """Close a worked row: confirmed | ruled_out | open_proof_gap."""
        if outcome not in ("confirmed", "ruled_out", "open_proof_gap"):
            raise CampaignError(f"invalid closure outcome {outcome!r}")
        return self._move(self.get(row_id), "working", outcome)

    # -- the gate -----------------------------------------------------------
    def record_gate(self, row_id: int, answers: dict) -> Row:
        row = self.get(row_id)
        if row.state != "confirmed":
            raise CampaignError(f"row {row.id} must be 'confirmed' before the gate")
        missing = [q for q in GATE_QUESTIONS if q not in answers]
        if missing:
            raise CampaignError(f"gate answers missing: {', '.join(missing)}")
        row.gate = {q: bool(answers[q]) for q in GATE_QUESTIONS}
        if all(row.gate.values()):
            row.state = "gated"
        else:
            failed = [q for q, ok in row.gate.items() if not ok]
            row.notes.append(f"gate failed: {', '.join(failed)}")
            row.state = "killed"
        return row

    # -- dedupe -------------------------------------------------------------
    def record_dedupe(self, row_id: int, sources: list) -> Row:
        row = self.get(row_id)
        if row.state != "gated":
            raise CampaignError(f"row {row.id} must be 'gated' before dedupe")
        clean = [s.strip() for s in sources if s and s.strip()]
        if len(clean) < MIN_DEDUPE_SOURCES:
            raise CampaignError(
                f"dedupe needs at least {MIN_DEDUPE_SOURCES} recorded sources, got {len(clean)}"
            )
        row.dedupe_sources = clean
        row.state = "deduped"
        return row

    def mark_reported(self, row_id: int) -> Row:
        return self._move(self.get(row_id), "deduped", "reported")

    # -- submission -----------------------------------------------------------
    def brake_tripped(self) -> bool:
        known = [r for r in self.rows if r.outcome in OUTCOMES]
        if len(known) < BRAKE_MIN_OUTCOMES:
            return False
        bad = sum(1 for r in known if r.outcome in ("duplicate", "na"))
        return (bad / len(known)) > BRAKE_MAX_BAD_RATIO

    def submit(self, row_id: int, approved: bool = False) -> Row:
        row = self.get(row_id)
        if row.state != "reported":
            raise CampaignError(f"row {row.id} must be 'reported' before submission")
        if not self.autopilot and not approved:
            raise ApprovalRequired(
                "submission needs autopilot mode or explicit operator approval"
            )
        if self.autopilot and self.brake_tripped():
            raise BrakeEngaged(
                "validity brake engaged: N/A + duplicate ratio too high; autopilot halted"
            )
        row.state = "submitted"
        return row

    def record_outcome(self, row_id: int, outcome: str) -> Row:
        row = self.get(row_id)
        if outcome not in OUTCOMES:
            raise CampaignError(f"invalid outcome {outcome!r}")
        if row.state != "submitted":
            raise CampaignError(f"row {row.id} must be 'submitted' to record an outcome")
        row.outcome = outcome
        return row

    # -- views / persistence --------------------------------------------------
    def next_row(self) -> Row | None:
        for state in ("working", "queued"):
            for row in self.rows:
                if row.state == state:
                    return row
        return None

    def board(self) -> dict:
        counts = {state: 0 for state in ROW_STATES}
        for row in self.rows:
            counts[row.state] += 1
        return counts

    def to_json(self) -> str:
        data = {
            "autopilot": self.autopilot,
            "next_id": self._next_id,
            "scope": {
                "program": self.scope.program,
                "in_scope": self.scope.in_scope,
                "out_of_scope": self.scope.out_of_scope,
            },
            "rows": [asdict(r) for r in self.rows],
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Campaign":
        data = json.loads(text)
        scope = Scope(
            in_scope=data["scope"]["in_scope"],
            out_of_scope=data["scope"]["out_of_scope"],
            program=data["scope"].get("program", ""),
        )
        campaign = cls(scope=scope, autopilot=data.get("autopilot", False))
        campaign._next_id = data.get("next_id", 1)
        campaign.rows = [Row(**r) for r in data.get("rows", [])]
        return campaign
