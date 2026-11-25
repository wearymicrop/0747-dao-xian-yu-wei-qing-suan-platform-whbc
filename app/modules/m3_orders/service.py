from collections import defaultdict

from app.modules.m3_orders.events import event_fields, event_time
from app.quality import issue, rows


def group_events(items, identity, comparison, conflict, duplicate):
    buckets = defaultdict(list)
    for item in items:
        buckets[identity(item)].append(item)
    kept, isolated, ignored = [], [], []
    for bucket in buckets.values():
        bucket.sort(key=lambda item: (event_time(item), item["row"]))
        first, *rest = bucket
        if any(comparison(item) != comparison(first) for item in rest):
            isolated.extend(
                issue(conflict, item["row"], item["raw"]) for item in bucket
            )
            continue
        kept.append(first)
        ignored.extend(
            issue(duplicate, item["row"], item["raw"], kept=first["row"])
            for item in rest
        )
    return kept, isolated, ignored


def collect(data, as_of):
    input_rows = list(rows(data, "events"))
    parsed, isolated, notices = [], [], []
    high = None
    for row, raw in input_rows:
        try:
            item = event_fields(raw)
        except (KeyError, ValueError, TypeError):
            isolated.append(issue("BAD_EVENT", row, raw))
            continue
        if item["received"] > as_of:
            isolated.append(issue("FUTURE_EVENT", row, raw))
            continue
        if high is not None and item["time"] < high:
            notices.append(issue("LATE_ARRIVAL", row, raw))
        high = max(high or item["time"], item["time"])
        parsed.append(dict(item, row=row, raw=raw))
    unique, conflicts, duplicates = group_events(
        parsed,
        lambda item: item["id"],
        lambda item: {
            k: v for k, v in item.items() if k not in {"row", "raw", "received"}
        },
        "EVENT_CONFLICT",
        "DUPLICATE_EVENT",
    )
    payments, pay_conflicts, pay_duplicates = group_events(
        [row for row in unique if row["type"] == "pay"],
        lambda item: item["payment"],
        lambda item: tuple(item[k] for k in ("order", "trip", "tier", "group")),
        "PAYMENT_CONFLICT",
        "DUPLICATE_PAYMENT",
    )
    accepted = sorted(
        [row for row in unique if row["type"] != "pay"] + payments,
        key=lambda item: (event_time(item), item["row"]),
    )
    errors, ignored = isolated + conflicts + pay_conflicts, duplicates + pay_duplicates
    return {
        "events": accepted,
        "isolated": errors,
        "duplicates": ignored,
        "notices": notices,
        "counts": {
            "input": len(input_rows),
            "accepted": len(accepted),
            "isolated": len(errors),
            "duplicate": len(ignored),
        },
    }
