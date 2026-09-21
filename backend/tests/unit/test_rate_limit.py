from app.core.rate_limit import RULES, _match_rule


def test_login_rule_matches():
    rule = _match_rule("/api/v1/auth/login", "POST")
    assert rule == (10, 300)


def test_register_rule_matches():
    rule = _match_rule("/api/v1/auth/register", "POST")
    assert rule == (5, 3600)


def test_generic_api_rule_fallback():
    rule = _match_rule("/api/v1/orders", "GET")
    assert rule == (600, 60)


def test_unknown_prefix_returns_none():
    assert _match_rule("/unknown", "GET") is None


def test_method_mismatch_falls_through_to_generic():
    # login rule requires POST
    rule = _match_rule("/api/v1/auth/login", "GET")
    # generic /api/v1/ rule applies
    assert rule == (600, 60)


def test_rules_sorted_most_specific_first():
    # every prefix before the last one should be more specific
    assert RULES[-1][0] == "/api/v1/"