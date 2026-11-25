from app.modules.m1_sailings.windows import bookable
from app.modules.m2_seats.contract import allowed


def eligibility(event, time, state):
    trip, tier = event["trip"], event["tier"]
    seat = state["tiers"].get(trip, {}).get(tier)
    if seat is None:
        return "UNKNOWN_SEAT"
    if not allowed(seat, event["group"]):
        return "NOT_ELIGIBLE"
    if not bookable(state["sailings"][trip], time):
        return "BOOKING_CLOSED"
    return None


def free_seat(event, state):
    return state["remaining"][event["trip"], event["tier"]] > 0
