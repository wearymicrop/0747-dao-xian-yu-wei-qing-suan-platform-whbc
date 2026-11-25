from collections import defaultdict

from app.modules.m3_orders.events import event_time
from app.modules.m4_transfers.tickets import find_seat, original, ticket
from app.modules.m5_waitlist.service import advance, enroll, outcome
from app.quality import issue


def move(event, time, state):
    order, trip, tier = event["order"], event["trip"], event["tier"]
    tickets = state["tickets"]
    current = original(event, tickets)
    entry = {
        "event": event["id"],
        "row": event["row"],
        "order": order,
        "time": time,
        "from": current,
        "to": None,
        "requested_trip": trip,
        "target_trip": event.get("to_trip"),
    }
    code = None
    if current is None:
        code = "STALE_TICKET"
    elif event["type"] == "refund":
        if time >= state["sailings"][trip]["refund_until"]:
            code = "LATE_REFUND"
        else:
            del tickets[order]
            state["remaining"][trip, tier] += 1
    else:
        destination = event["to_trip"], event["to_tier"]
        if destination == (trip, tier):
            code = "SELF_SWAP"
        elif time >= state["sailings"][trip]["close"]:
            code = "BOOKING_CLOSED"
        else:
            code = find_seat(event, *destination, time, state)
            if not code:
                new = ticket(event, *destination, time, event["id"])
                state["remaining"][destination] -= 1
                state["remaining"][trip, tier] += 1
                tickets[order] = new
                entry["to"] = new
    entry.update(
        code=code, status="REJECTED" if code else "APPLIED", action=event["type"]
    )
    state["moves"].append(entry)
    return code


def occupy(event, time, state):
    order, trip, tier = event["order"], event["trip"], event["tier"]
    hold = state["holds"].get(order)
    own_hold = hold is not None and all(
        hold[k] == event[k] for k in ("trip", "tier", "group")
    )
    is_pay = event["type"] == "pay"
    if order in state["tickets"] or (hold and not (own_hold and is_pay)):
        return "ORDER_ACTIVE"
    code = find_seat(event, trip, tier, time, state, allow_full=own_hold)
    if code:
        return code
    proof = ticket(event, trip, tier, time, event["id"])
    if not own_hold:
        state["remaining"][trip, tier] -= 1
    if is_pay:
        state["holds"].pop(order, None)
        state["tickets"][order] = proof
    else:
        state["holds"][order] = dict(proof, expires=event["expires"])
    return None


def replay(sailings, capacity, orders):
    times = defaultdict(list)
    times[sailings["as_of"]]
    for event in orders["events"]:
        times[event_time(event)].append(event)
        if event["type"] == "hold" and event["expires"] <= sailings["as_of"]:
            times[event["expires"]]
    remaining = {
        (trip, tier): seat["capacity"]
        for trip, tiers in capacity["tiers"].items()
        for tier, seat in tiers.items()
    }
    state = {
        "remaining": remaining,
        "sailings": sailings["sailings"],
        "tiers": capacity["tiers"],
        "tickets": {},
        "holds": {},
        "moves": [],
        "queue": {},
        "promoted": [],
        "expired": [],
        "isolated": [],
        "applied": [],
    }
    for time, events in sorted(times.items()):
        expired = [
            order for order, hold in state["holds"].items() if hold["expires"] <= time
        ]
        for order in expired:
            hold = state["holds"].pop(order)
            state["remaining"][hold["trip"], hold["tier"]] += 1
            state["expired"].append(dict(hold, code="HOLD_EXPIRED", released_at=time))
        if expired:
            advance(time, state)
        for event in events:
            if event["type"] == "wait":
                code = enroll(event, time, state)
            elif event["type"] in {"swap", "refund"}:
                code = move(event, time, state)
            else:
                code = occupy(event, time, state)
            if code:
                state["isolated"].append(
                    issue(code, event["row"], event["raw"], order=event["order"])
                )
            else:
                state["applied"].append(
                    {"event": event["id"], "row": event["row"], "time": time}
                )
            advance(time, state)
    return (
        {
            "tickets": list(state["tickets"].values()),
            "holds": list(state["holds"].values()),
            "moves": state["moves"],
            "expired_holds": state["expired"],
            "isolated": state["isolated"],
            "applied": state["applied"],
        },
        outcome(state, sailings["as_of"]),
    )
