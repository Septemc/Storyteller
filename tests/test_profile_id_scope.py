from backend.core.tenant import scoped_default_id


def test_scoped_default_id_for_user():
    assert scoped_default_id("preset_default", "u1") == "preset_default__u1"
    assert scoped_default_id("regex_default", "u2") == "regex_default__u2"


def test_scoped_default_id_for_public():
    assert scoped_default_id("preset_default", None) == "preset_default"
