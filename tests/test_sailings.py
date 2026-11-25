import pytest
from app.errors import BusinessError
from app.modules.m1_sailings.service import schedule
from app.modules.m1_sailings.windows import bookable


def test_two_routes_at_cutoff(clean_result):
    routes = clean_result["sailings"]["sailings"]
    assert {key: row["bookable"] for key, row in routes.items()} == {
        "NL-0910": False,
        "NB-1040": True,
    }


def test_exact_booking_boundary(clean_result):
    row = clean_result["sailings"]["sailings"]["NL-0910"]
    assert bookable(row, row["open"]) and not bookable(row, row["close"])


def test_sailed_boundary(clean):
    clean["as_of"] = clean["sailings"][0]["departure"]
    assert schedule(clean)["sailings"]["NL-0910"]["sailed"] is True


def test_bad_cutoff_requires_offset(clean):
    clean["as_of"] = "2026-11-20T09:08:00"
    with pytest.raises(BusinessError, match="须带时区"):
        schedule(clean)


def test_inverted_window_isolated(clean):
    clean["sailings"][0]["close"] = clean["sailings"][0]["open"]
    assert schedule(clean)["isolated"][0]["code"] == "BAD_SAILING"


def test_overlapping_sailing_id_conflicting(clean):
    # TRAP-25
    clean["sailings"].append(dict(clean["sailings"][0], destination="小岛"))
    result = schedule(clean)
    assert [line["row"] for line in result["isolated"]] == [
        1,
        3,
    ] and "NL-0910" not in result["sailings"]
