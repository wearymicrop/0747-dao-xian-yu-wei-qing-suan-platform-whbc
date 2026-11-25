import pytest
from app.errors import BusinessError
from app.modules.m6_reconcile.service import reconcile
from app.modules.m7_archive.signoff import approval


def audit(result):
    return reconcile(result["seats"], result["orders"], result["transfers"])


def test_dirty_ledger_exact_capacity(dirty_result):
    result = audit(dirty_result)
    assert (
        result["totals"] == {"capacity": 21, "issued": 18, "held": 2, "open": 1}
        and result["status"] == "MATCHED"
    )


def test_clean_every_tier_balanced(clean_result):
    result = audit(clean_result)
    assert len(result["tiers"]) == 4 and all(
        r["capacity"] == r["issued"] + r["held"] + r["open"] for r in result["tiers"]
    )


def test_no_aggregating_away_overbooked_class(clean_result):
    clean_result["seats"]["tiers"]["NL-0910"]["客舱"]["capacity"] = 7
    assert audit(clean_result)["status"] == "MISMATCH"


def test_orphan_ticket_detected(clean_result):
    clean_result["transfers"]["tickets"][0]["tier"] = "缺失层级"
    assert audit(clean_result)["orphan_seats"] == 1


def test_duplicate_order_detected(clean_result):
    clean_result["transfers"]["holds"].append(clean_result["transfers"]["tickets"][0])
    assert audit(clean_result)["duplicate_orders"] == 1


def test_every_accepted_order_is_accounted_for(dirty_result):
    dirty_result["transfers"]["applied"].pop()
    result = audit(dirty_result)
    assert result["event_difference"] == 1 and result["status"] == "MISMATCH"


def test_signoff_refuses_unbalanced_and_preserves_review(dirty_result):
    assert approval(dirty_result)["status"] == "NOTED"
    dirty_result["reconcile"]["status"] = "MISMATCH"
    with pytest.raises(BusinessError, match="尚未对平"):
        approval(dirty_result)
