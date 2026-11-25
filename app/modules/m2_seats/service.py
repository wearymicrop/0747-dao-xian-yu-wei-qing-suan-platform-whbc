from collections import defaultdict

from app.modules.m2_seats.contract import define
from app.quality import issue, rows


def capacity(data, schedule):
    buckets, isolated = defaultdict(list), []
    for row, raw in rows(data, "capacities"):
        try:
            item = define(raw, schedule["sailings"])
            buckets[item["trip"], item["tier"]].append((row, raw, item))
        except (KeyError, ValueError, TypeError):
            isolated.append(issue("BAD_TIER", row, raw))
    valid = {trip: {} for trip in schedule["sailings"]}
    for (trip, tier), items in buckets.items():
        if len(items) > 1:
            isolated.extend(issue("TIER_CONFLICT", row, raw) for row, raw, _ in items)
            continue
        row, _, item = items[0]
        valid[trip][tier] = dict(item, row=row)
    return {
        "tiers": valid,
        "isolated": isolated,
        "capacity": sum(
            seat["capacity"] for tiers in valid.values() for seat in tiers.values()
        ),
    }
