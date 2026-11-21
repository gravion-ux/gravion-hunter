import pytest

from gravion_hunter.scope import Scope, ScopeError

SAMPLE = """# Example Programme
## In scope
- example.com
- *.example.com
- api.example.net
## Out of scope
- staging.example.com
- login.example.com
"""


@pytest.fixture
def scope():
    return Scope.from_text(SAMPLE)


def test_program_name_parsed(scope):
    assert scope.program == "Example Programme"


def test_exact_host_in_scope(scope):
    assert scope.check("example.com")
    assert scope.check("api.example.net")


def test_wildcard_matches_subdomains(scope):
    assert scope.check("app.example.com")
    assert scope.check("deep.app.example.com")


def test_wildcard_does_not_match_base(scope):
    # *.example.com alone would not cover the base; the exact entry does here,
    # so use a scope with only the wildcard.
    s = Scope.from_text("## In scope\n- *.example.com\n")
    assert not s.check("example.com")
    assert s.check("a.example.com")


def test_out_of_scope_wins_over_wildcard(scope):
    assert not scope.check("staging.example.com")
    assert not scope.check("login.example.com")


def test_unrelated_host_rejected(scope):
    assert not scope.check("evil.com")
    assert not scope.check("example.com.evil.com")
    assert not scope.check("notexample.com")


def test_url_input_normalised(scope):
    assert scope.check("https://app.example.com/path?q=1")
    assert scope.check("https://api.example.net:8443/v1")


def test_empty_in_scope_refused():
    with pytest.raises(ScopeError):
        Scope.from_text("# Nothing here\n## Out of scope\n- x.com\n")


def test_require_returns_host(scope):
    assert scope.require("https://app.example.com/x") == "app.example.com"


def test_require_raises_for_out_of_scope(scope):
    with pytest.raises(ScopeError):
        scope.require("staging.example.com")
