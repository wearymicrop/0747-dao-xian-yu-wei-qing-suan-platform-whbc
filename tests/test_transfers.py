from app.pipeline import calculate


def test_exchange_releases_and_occupies_atomically(dirty_result):
    record = dirty_result["transfers"]
    swap = record["moves"][0]
    assert (swap["from"]["trip"], swap["to"]["trip"]) == ("NL-0910", "NB-1040")
    assert [
        (r["trip"], r["ticket"]) for r in record["tickets"] if r["order"] == "0001"
    ] == [("NB-1040", "S1")]


def test_failed_exchange_retains_original(dirty_result):
    record = dirty_result["transfers"]
    swap = next(r for r in record["moves"] if r["event"] == "S2")
    assert swap["code"] == "NO_CAPACITY" and any(
        r["ticket"] == "A04" for r in record["tickets"]
    )


def test_stale_ticket_rejected(dirty_result):
    # TRAP-26
    assert (
        next(r for r in dirty_result["transfers"]["moves"] if r["event"] == "S3")[
            "code"
        ]
        == "STALE_TICKET"
    )


def test_received_late_refund_never_releases(dirty_result):
    # TRAP-13
    transfers = dirty_result["transfers"]
    assert transfers["moves"][-1]["code"] == "LATE_REFUND" and any(
        r["ticket"] == "A03" for r in transfers["tickets"]
    )


def test_same_seat_swap_rejected(clean):
    # TRAP-20
    event = next(row for row in clean["events"] if row["id"] == "S1")
    event["to_trip"] = event["trip"]
    assert calculate(clean)["transfers"]["moves"][0]["code"] == "SELF_SWAP"


def test_held_seat_payment_uses_its_own_slot(clean):
    event = next(row for row in clean["events"] if row["id"] == "H1")
    confirmation = {key: event[key] for key in ("order", "trip", "tier", "group")}
    clean["events"].append(
        dict(
            confirmation,
            id="PH1",
            type="pay",
            payment="P-PH1",
            time="2026-11-20T08:30:00+08:00",
        )
    )
    result = calculate(clean)["transfers"]
    assert [r["ticket"] for r in result["tickets"] if r["order"] == "0053"] == ["PH1"]
    assert [r["order"] for r in result["holds"]] == ["0054"]
