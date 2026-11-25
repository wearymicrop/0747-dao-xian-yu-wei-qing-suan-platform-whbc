from app.pipeline import calculate


def test_duplicate_payment_recorded_once(dirty_result):
    orders = dirty_result["orders"]
    assert orders["counts"] == {
        "input": 33,
        "accepted": 31,
        "isolated": 1,
        "duplicate": 1,
    }
    assert (
        orders["duplicates"][0]["code"] == "DUPLICATE_PAYMENT"
        and orders["duplicates"][0]["kept"] == 1
    )


def test_payment_used_on_other_order_quarantined(clean):
    # TRAP-14
    clean["events"].append(dict(clean["events"][0], id="ERR", order="0099"))
    orders = calculate(clean)["orders"]
    assert [item["row"] for item in orders["isolated"]] == [1, 23]
    assert all(item["code"] == "PAYMENT_CONFLICT" for item in orders["isolated"])


def test_same_event_id_different_content_quarantined(clean):
    clean["events"].append(dict(clean["events"][0], order="0099"))
    assert [r["code"] for r in calculate(clean)["orders"]["isolated"]] == [
        "EVENT_CONFLICT"
    ] * 2


def test_identical_events_with_different_offsets_merge(clean):
    # TRAP-11
    clean["events"].append(dict(clean["events"][0], time="2026-11-19T23:10:00Z"))
    assert calculate(clean)["orders"]["duplicates"][0]["code"] == "DUPLICATE_EVENT"


def test_old_event_is_reordered_and_zeros_preserved(dirty_result):
    # TRAP-08
    orders = dirty_result["orders"]
    assert orders["events"][0]["order"] == "0001" and "LATE_ARRIVAL" in {
        r["code"] for r in orders["notices"]
    }


def test_future_callback_isolated(dirty_result):
    assert dirty_result["orders"]["isolated"][0]["code"] == "FUTURE_EVENT"
