import pytest

from waste_heat_model.config import (
    PlaceholderError,
    load_config,
    provenance_note,
    unverified,
    values,
)


def test_loads_all_scenarios():
    for s in ("conservative", "central", "optimistic"):
        v = values(load_config(s))
        assert v["data_centre.it_heat_kw"] == 700


def test_strict_mode_blocks_placeholders():
    with pytest.raises(PlaceholderError):
        load_config("central", strict=True)


def test_mock_values_are_flagged():
    # The data-centre numbers come from the MOCK data pack, so they must be flagged.
    flags = unverified(load_config("central"))
    assert "data_centre.it_heat_kw" in flags["mock"]
    assert "emitters.radiator.q_nom_kw" in flags["placeholder"]


def test_provenance_note_names_the_counts():
    flat = load_config("central")
    note = provenance_note(flat)
    assert note.startswith("UNVERIFIED INPUTS")
    assert f"{len(unverified(flat)['mock'])} mock" in note


def test_provenance_note_when_everything_is_verified():
    flat = {"a.b": {"value": 1, "unit": "-", "source": "x", "status": "literature"}}
    assert unverified(flat) == {}
    assert provenance_note(flat) == "All inputs verified."

