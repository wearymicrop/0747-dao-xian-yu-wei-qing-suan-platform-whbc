from app.pipeline import calculate
from app.quality import instant


def test_fifo_first_when_exchange_frees_capacity(dirty_result):
    queue = dirty_result["waitlist"]["promoted"]
    assert [r["order"] for r in queue[:2]] == ["0051", "0052"] and queue[0][
        "promoted_at"
    ] < queue[1]["promoted_at"]


def test_ineligible_does_not_block_restricted_queue(dirty_result):
    # TRAP-19
    queue = {r["order"]: r for r in dirty_result["waitlist"]["queue"]}
    assert (
        queue["0061"]["code"] == "NOT_ELIGIBLE" and queue["0062"]["state"] == "PROMOTED"
    )


def test_expiration_promotes_at_expiry_not_later(dirty_result):
    # TRAP-23
    transfers = dirty_result["transfers"]
    assert [r["code"] for r in transfers["expired_holds"]] == ["HOLD_EXPIRED"] * 2
    promoted = dirty_result["waitlist"]["promoted"][-1]
    assert (
        promoted["promoted_at"] == instant("2026-11-20T09:06:00+08:00")
        and promoted["order"] == "0064"
    )


def test_pending_closes_without_using_other_tier(clean):
    clean["events"] = [
        r for r in clean["events"] if r["type"] not in ("swap", "refund")
    ]
    result = calculate(clean)["waitlist"]
    assert result["counts"]["closed"] == 2 and result["counts"]["promoted"] == 0


def test_tie_respects_source_sequence(clean):
    events = {r["id"]: r for r in clean["events"]}
    events["Q2"]["time"] = events["Q1"]["time"]
    assert [r["id"] for r in calculate(clean)["waitlist"]["promoted"]] == ["Q1", "Q2"]


def test_same_order_cannot_enroll_twice(clean):
    event = next(r for r in clean["events"] if r["id"] == "Q1")
    clean["events"].append(dict(event, id="Q1-BIS"))
    result = calculate(clean)
    assert result["waitlist"]["counts"]["promoted"] == 2
    assert result["transfers"]["isolated"][0]["code"] == "WAIT_DUPLICATE"
