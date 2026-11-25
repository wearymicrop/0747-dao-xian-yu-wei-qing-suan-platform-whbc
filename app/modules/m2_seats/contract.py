from app.quality import integer, token


def define(raw, sailings):
    trip, tier = token(raw["trip"]), token(raw["tier"])
    if trip not in sailings or not isinstance(raw["groups"], list):
        raise ValueError
    groups = sorted(set(token(group) for group in raw["groups"]))
    if not groups:
        raise ValueError
    return {
        "trip": trip,
        "tier": tier,
        "groups": groups,
        "capacity": integer(raw["capacity"], 0, 10000),
    }


def allowed(seat, group):
    return "通用" in seat["groups"] or group in seat["groups"]


def available(seat, tickets, holds):
    key = (seat["trip"], seat["tier"])
    return seat["capacity"] - sum(
        (state["trip"], state["tier"]) == key
        for pool in (tickets, holds)
        for state in pool.values()
    )
