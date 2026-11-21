import pytest

from gravion_hunter.campaign import (
    GATE_QUESTIONS,
    ApprovalRequired,
    BrakeEngaged,
    Campaign,
    CampaignError,
)
from gravion_hunter.scope import Scope, ScopeError

SCOPE_TEXT = """# Test Programme
## In scope
- *.example.com
- example.com
## Out of scope
- staging.example.com
"""

ALL_PASS = {q: True for q in GATE_QUESTIONS}
SOURCES = ["programme-disclosed", "vendor-changelog", "cve-db"]


@pytest.fixture
def campaign():
    return Campaign(scope=Scope.from_text(SCOPE_TEXT))


@pytest.fixture
def autopilot():
    return Campaign(scope=Scope.from_text(SCOPE_TEXT), autopilot=True)


def _confirmed(c: Campaign) -> int:
    row = c.add_row("app.example.com", "idor", "/v1/orders/{id}")
    c.start(row.id)
    c.close(row.id, "confirmed")
    return row.id


def _reported(c: Campaign) -> int:
    rid = _confirmed(c)
    c.record_gate(rid, ALL_PASS)
    c.record_dedupe(rid, SOURCES)
    c.mark_reported(rid)
    return rid


def test_add_row_in_scope(campaign):
    row = campaign.add_row("app.example.com", "ssrf", "/fetch")
    assert row.state == "queued"
    assert row.host == "app.example.com"


def test_add_row_out_of_scope_rejected(campaign):
    with pytest.raises(ScopeError):
        campaign.add_row("staging.example.com", "ssrf", "/fetch")
    with pytest.raises(ScopeError):
        campaign.add_row("other.org", "ssrf", "/fetch")


def test_full_pipeline_with_approval(campaign):
    rid = _reported(campaign)
    row = campaign.submit(rid, approved=True)
    assert row.state == "submitted"
    campaign.record_outcome(rid, "valid")
    assert campaign.get(rid).outcome == "valid"


def test_submit_without_autopilot_or_approval_blocked(campaign):
    rid = _reported(campaign)
    with pytest.raises(ApprovalRequired):
        campaign.submit(rid)


def test_autopilot_submit_allowed(autopilot):
    rid = _reported(autopilot)
    assert autopilot.submit(rid).state == "submitted"


def test_gate_all_pass_moves_to_gated(campaign):
    rid = _confirmed(campaign)
    assert campaign.record_gate(rid, ALL_PASS).state == "gated"


def test_gate_one_failure_kills_row(campaign):
    rid = _confirmed(campaign)
    answers = dict(ALL_PASS, impact_proven=False)
    row = campaign.record_gate(rid, answers)
    assert row.state == "killed"
    assert "impact_proven" in row.notes[-1]


def test_gate_missing_answers_rejected(campaign):
    rid = _confirmed(campaign)
    with pytest.raises(CampaignError):
        campaign.record_gate(rid, {"exploitable_now": True})


def test_gate_requires_confirmed_state(campaign):
    row = campaign.add_row("app.example.com", "xss", "/search")
    with pytest.raises(CampaignError):
        campaign.record_gate(row.id, ALL_PASS)


def test_dedupe_needs_three_sources(campaign):
    rid = _confirmed(campaign)
    campaign.record_gate(rid, ALL_PASS)
    with pytest.raises(CampaignError):
        campaign.record_dedupe(rid, ["only-one", "two"])
    assert campaign.record_dedupe(rid, SOURCES).state == "deduped"


def test_illegal_transition_rejected(campaign):
    row = campaign.add_row("app.example.com", "xss", "/search")
    with pytest.raises(CampaignError):
        campaign.mark_reported(row.id)


def test_close_outcomes(campaign):
    for outcome in ("ruled_out", "open_proof_gap"):
        row = campaign.add_row("app.example.com", "sqli", "/item")
        campaign.start(row.id)
        assert campaign.close(row.id, outcome).state == outcome


def test_brake_trips_on_bad_ratio(autopilot):
    # 6 outcomes: 2 bad of first 5 keeps ratio at 0.4 > 0.30 once >=5 known.
    for i in range(5):
        rid = _reported(autopilot)
        autopilot.submit(rid)
        autopilot.record_outcome(rid, "na" if i < 2 else "valid")
    assert autopilot.brake_tripped()
    rid = _reported(autopilot)
    with pytest.raises(BrakeEngaged):
        autopilot.submit(rid)


def test_brake_not_tripped_when_ratio_healthy(autopilot):
    for i in range(6):
        rid = _reported(autopilot)
        autopilot.submit(rid)
        autopilot.record_outcome(rid, "duplicate" if i == 0 else "valid")
    assert not autopilot.brake_tripped()


def test_next_row_prefers_working(campaign):
    a = campaign.add_row("app.example.com", "xss", "/a")
    b = campaign.add_row("app.example.com", "xss", "/b")
    campaign.start(b.id)
    assert campaign.next_row().id == b.id
    campaign.close(b.id, "ruled_out")
    assert campaign.next_row().id == a.id


def test_json_round_trip(campaign):
    rid = _reported(campaign)
    clone = Campaign.from_json(campaign.to_json())
    assert clone.get(rid).state == "reported"
    assert clone.scope.check("app.example.com")
    assert not clone.scope.check("staging.example.com")
