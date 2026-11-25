from app.modules.m2_seats.contract import allowed, available
from app.pipeline import calculate


def test_capacity_by_tier(clean_result):
    seats = clean_result["seats"]
    assert (
        seats["tiers"]["NL-0910"]["客舱"]["capacity"] == 8 and seats["capacity"] == 21
    )


def test_restricted_group(clean_result):
    seat = clean_result["seats"]["tiers"]["NL-0910"]["无障碍"]
    assert allowed(seat, "轮椅") and not allowed(seat, "普通")


def test_open_class_allows_special_group(clean_result):
    assert allowed(clean_result["seats"]["tiers"]["NL-0910"]["客舱"], "轮椅")


def test_duplicate_tier_entirely_isolated(clean):
    clean["capacities"].append(dict(clean["capacities"][0], capacity=99))
    seats = calculate(clean)["seats"]
    assert seats["capacity"] == 13 and all(
        line["code"] == "TIER_CONFLICT" for line in seats["isolated"]
    )


def test_unknown_trip_capacity_isolated(clean):
    clean["capacities"].append(dict(clean["capacities"][0], trip="unknown"))
    assert calculate(clean)["seats"]["isolated"][0]["code"] == "BAD_TIER"


def test_capacity_subtracts_holds(dirty_result):
    seat = dirty_result["seats"]["tiers"]["NB-1040"]["客舱"]
    ledger = dirty_result["transfers"]
    assert (
        available(
            seat,
            {r["order"]: r for r in ledger["tickets"]},
            {r["order"]: r for r in ledger["holds"]},
        )
        == 0
    )
