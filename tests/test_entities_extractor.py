from demon_cry.services.entities import (
    TYPE_MAX,
    canonical_json,
    extract_entities,
    normalize_type,
)


def test_list_shape_and_field_consumption():
    drafts = extract_entities([{"type": "IP", "value": " 1.2.3.4 ", "asn": 13335}])
    assert drafts == [{"type": "ip", "value": "1.2.3.4", "data": {"asn": 13335}}]


def test_type_aliases():
    d1 = extract_entities([{"entity_type": "Domain", "value": "x"}])[0]
    assert d1["type"] == "domain"
    d2 = extract_entities([{"kind": "eMail", "value": "y"}])[0]
    assert d2["type"] == "email"
    # приоритет: type > entity_type > kind
    i1 = extract_entities([{"type": "t1", "entity_type": "t2", "kind": "t3"}])[0]
    assert i1["type"] == "t1"
    i2 = extract_entities([{"entity_type": "t2", "kind": "t3"}])[0]
    assert i2["type"] == "t2"


def test_value_aliases():
    assert extract_entities([{"indicator": "A", "value": "B"}])[0]["value"] == "B"
    assert extract_entities([{"identifier": "A"}])[0]["value"] == "A"
    assert extract_entities([{"target": "A", "id": 1}])[0]["value"] == "A"
    assert extract_entities([{"data": "A", "other": 2}])[0]["value"] == "A"


def test_non_string_value_candidates_fall_back():
    drafts = extract_entities([{"value": 8080}])
    assert drafts[0]["value"] == canonical_json({"value": 8080})
    assert drafts[0]["data"]["normalized"] is False


def test_fallback_without_value():
    item = {"asn": 13335, "org": "cf"}
    drafts = extract_entities([item])
    assert drafts[0]["value"] == canonical_json(item)
    assert drafts[0]["data"]["normalized"] is False


def test_fallback_keeps_unused_keys_in_data():
    item = {"type": "ip", "value": None, "x": 1}
    drafts = extract_entities([item])
    # value=None не потреблён; fallback = canonical JSON всего элемента
    assert drafts[0]["type"] == "ip"
    assert drafts[0]["value"] == canonical_json(item)
    assert drafts[0]["data"] == {"value": None, "x": 1, "normalized": False}


def test_legacy_wrapper_dict_data_list():
    raw = {"data": [{"type": "domain", "value": "example.com"}]}
    assert extract_entities(raw) == [
        {"type": "domain", "value": "example.com", "data": {}}
    ]


def test_scalar_list_entries():
    drafts = extract_entities(["8.8.8.8", 80, None, [1, 2]])
    assert drafts[:2] == [
        {"type": None, "value": "8.8.8.8", "data": {}},
        {"type": None, "value": "80", "data": {}},
    ]
    assert len(drafts) == 2


def test_legacy_dict_map():
    assert extract_entities({"ip": "1.1.1.1"}) == [
        {"type": "ip", "value": "1.1.1.1", "data": {}}
    ]


def test_legacy_dict_map_scalar_values():
    drafts = extract_entities({"port": 22})
    assert drafts == [{"type": "port", "value": "22", "data": {}}]


def test_legacy_dict_map_nested_dict():
    drafts = extract_entities({"ip": {"value": "1.1.1.1", "asn": 1}})
    assert drafts == [
        {"type": "ip", "value": "1.1.1.1", "data": {"asn": 1, "normalized": True}}
    ]


def test_nested_dict_without_inner_value_falls_back():
    drafts = extract_entities({"ip": {"x": 1}})
    assert drafts[0] == {
        "type": "ip",
        "value": canonical_json({"type": "ip", "x": 1}),
        "data": {"x": 1, "normalized": False},
    }


def test_data_marker_not_dangling_on_success():
    drafts = extract_entities({"ip": {"value": "9.9.9.9", "normalized": "raw"}})
    assert drafts[0]["data"] == {"normalized": True}


def test_empty_shapes():
    assert extract_entities(None) == []
    assert extract_entities([]) == []
    assert extract_entities({}) == []
    assert extract_entities("str") == []


def test_normalize_type_slug_rules():
    assert normalize_type("IP Address") == "ip_address"
    assert normalize_type("  Person Name!! ") == "person_name"
    assert normalize_type("") is None
    assert normalize_type("---") is None
    assert normalize_type(None) is None
    long = "a" * (TYPE_MAX + 10)
    assert normalize_type(long) == "a" * TYPE_MAX
