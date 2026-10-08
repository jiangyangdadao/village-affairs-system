import pytest
from fastapi import HTTPException

from app import ledger_config


def test_get_ledger_unknown_returns_404():
    with pytest.raises(HTTPException) as e:
        ledger_config.get_ledger("not_exist")
    assert e.value.status_code == 404


def test_has_14_ledgers():
    assert len(ledger_config.LEDGER_LIST) == 14
    keys = {d.key for d in ledger_config.LEDGER_LIST}
    assert keys == {
        "resident", "poverty_alleviated", "monitoring", "dibao", "tekun",
        "disabled", "party", "veteran", "employment", "medical", "pension",
        "subsidy", "edu_aid", "med_aid",
    }


def test_resident_has_no_tag_type():
    assert ledger_config.get_ledger("resident").tag_type is None
    assert ledger_config.get_ledger("resident").scope == "person"


def test_household_tag_ledgers():
    for key in ["poverty_alleviated", "monitoring", "dibao", "tekun", "subsidy"]:
        d = ledger_config.get_ledger(key)
        assert d.scope == "household"
        assert d.tag_type == key


def test_person_tag_ledgers():
    for key in ["disabled", "party", "veteran", "employment", "medical", "pension",
                "edu_aid", "med_aid"]:
        d = ledger_config.get_ledger(key)
        assert d.scope == "person"
        assert d.tag_type == key


def test_monitoring_status_options():
    d = ledger_config.get_ledger("monitoring")
    assert d.status_options == ["风险未消除", "风险已消除"]
    assert d.status_default == "风险未消除"


def test_multi_ledgers_allow_multiple_rows():
    for key in ["employment", "edu_aid", "med_aid"]:
        assert ledger_config.get_ledger(key).multi
    assert not ledger_config.get_ledger("dibao").multi
    assert not ledger_config.get_ledger("subsidy").multi


def test_field_keys_unique_per_ledger():
    for d in ledger_config.LEDGER_LIST:
        keys = [f.key for f in d.fields]
        assert len(keys) == len(set(keys)), f"{d.key} 存在重复字段"


def test_select_fields_have_options():
    for d in ledger_config.LEDGER_LIST:
        for f in d.fields:
            if f.kind == "select":
                assert f.options, f"{d.key}.{f.key} 下拉字段缺少 options"
