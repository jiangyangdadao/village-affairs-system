def test_get_missing_key_returns_default(settings):
    assert settings.get("not_exist", "dft") == "dft"


def test_set_then_get(settings):
    settings.set("village_name", "青山村")
    assert settings.get("village_name") == "青山村"


def test_overwrite_existing(settings):
    settings.set("k", "1")
    settings.set("k", "2")
    assert settings.get("k") == "2"
