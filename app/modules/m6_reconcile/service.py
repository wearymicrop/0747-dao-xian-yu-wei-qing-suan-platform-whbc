from collections import Counter


def reconcile(seats, orders, transfers):
    issued = Counter((row["trip"], row["tier"]) for row in transfers["tickets"])
    kept = Counter((row["trip"], row["tier"]) for row in transfers["holds"])
    table = []
    for trip, tiers in sorted(seats["tiers"].items()):
        for tier, seat in sorted(tiers.items()):
            key = trip, tier
            tickets, holds, capacity = (
                issued.pop(key, 0),
                kept.pop(key, 0),
                seat["capacity"],
            )
            table.append(
                {
                    "trip": trip,
                    "tier": tier,
                    "capacity": capacity,
                    "issued": tickets,
                    "held": holds,
                    "open": capacity - tickets - holds,
                    "capacity_row": seat["row"],
                }
            )
    total = {
        key: sum(line[key] for line in table)
        for key in ("capacity", "issued", "held", "open")
    }
    counts = orders["counts"]
    input_delta = (
        counts["input"] - counts["accepted"] - counts["isolated"] - counts["duplicate"]
    )
    orphan = sum(issued.values()) + sum(kept.values())
    all_orders = [
        item["order"] for key in ("tickets", "holds") for item in transfers[key]
    ]
    duplicate = len(all_orders) - len(set(all_orders))
    event_delta = (
        counts["accepted"] - len(transfers["isolated"]) - len(transfers["applied"])
    )
    matched = not (
        event_delta
        or input_delta
        or orphan
        or duplicate
        or any(row["open"] < 0 for row in table)
    )
    return {
        "status": "MATCHED" if matched else "MISMATCH",
        "tiers": table,
        "totals": total,
        "order_row_difference": input_delta,
        "event_difference": event_delta,
        "orphan_seats": orphan,
        "duplicate_orders": duplicate,
    }
