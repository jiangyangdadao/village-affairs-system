import pytest
from fastapi import HTTPException

from app import ledger_config


def test_get_ledger_unknown_returns_404():
    with pytest.raises(HTTPException) as e:
        ledger_config.get_ledger("not_exist")
    assert e.value.status_code == 404


def test_has_11_ledgers():
    assert len(ledger_config.LEDGER_LIST) == 11
    keys = {d.key for d in ledger_config.LEDGER_LIST}
    assert keys == {
        "resident", "poverty_alleviated", "monitoring", "dibao", "tekun",
        "disabled", "party", "veteran", "employment", "medical", "pension",
    }


def test_resident_has_no_tag_type():
    assert ledger_config.get_ledger("resident").tag_type is None
    assert ledger_config.get_ledger("resident").scope == "person"


def test_household_tag_ledgers():
    for key in ["poverty_alleviated", "monitoring", "dibao", "tekun"]:
        d = ledger_config.get_ledger(key)
        assert d.scope == "household"
        assert d.tag_type == key


def test_person_tag_ledgers():
    for key in ["disabled", "party", "veteran", "employment", "medical", "pension"]:
        d = ledger_config.get_ledger(key)
        assert d.scope == "person"
        assert d.tag_type == key


def test_field_keys_unique_per_ledger():
    for d in ledger_config.LEDGER_LIST:
        keys = [f.key for f in d.fields]
        assert len(keys) == len(set(keys)), f"{d.key} 存在重复字段"


def test_select_fields_have_options():
    for d in ledger_config.LEDGER_LIST:
        for f in d.fields:
            if f.kind == "select":
                assert f.options, f"{d.key}.{f.key} 下拉字段缺少 options"
