from gravion_hunter.scope import Scope


def test_scope_entries_accept_urls_and_dedupe():
    scope = Scope.from_text("# P\n## In scope\n- https://Example.com:8443/login\n- example.com\n- *.example.com\n")
    assert scope.in_scope == ["example.com", "*.example.com"]
    assert scope.check("https://example.com/x")
    assert scope.check("a.example.com")
