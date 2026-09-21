from app.shared.filters import parse_sort


def test_parse_sort_desc():
    field, direction = parse_sort("-created_at")
    assert field == "created_at"
    assert direction == "desc"


def test_parse_sort_asc():
    field, direction = parse_sort("name")
    assert field == "name"
    assert direction == "asc"


def test_parse_sort_default():
    field, direction = parse_sort(None)
    assert field == "created_at"
    assert direction == "desc"