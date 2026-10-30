import pytest

from twhr.config import PlaceholderError, load_config, values


def test_loads_all_scenarios():
    for s in ("conservative", "central", "optimistic"):
        v = values(load_config(s))
        assert v["data_centre.it_heat_kw"] == 700


def test_strict_mode_blocks_placeholders():
    with pytest.raises(PlaceholderError):
        load_config("central", strict=True)
