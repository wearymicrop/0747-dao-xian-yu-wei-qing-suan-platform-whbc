from app.modules.m1_sailings.windows import bookable
from app.modules.m2_seats.contract import allowed


def find_seat(event, trip, tier, time, state, allow_full=False):
    seat = state["tiers"].get(trip, {}).get(tier)
    if seat is None:
        return "UNKNOWN_SEAT"
    if not allowed(seat, event["group"]):
        return "NOT_ELIGIBLE"
    if not bookable(state["sailings"][trip], time):
        return "BOOKING_CLOSED"
    if not allow_full and state["remaining"][trip, tier] <= 0:
        return "NO_CAPACITY"
    return None


def ticket(event, trip, tier, time, reference):
    return {
        "order": event["order"],
        "trip": trip,
        "tier": tier,
        "ticket": reference,
        "group": event["group"],
        "row": event["row"],
        "time": time,
    }


def original(event, tickets):
    current = tickets.get(event["order"])
    if current is None or any(
        current[key] != event[key] for key in ("trip", "tier", "ticket", "group")
    ):
        return None
    return current
