from app.modules.m5_waitlist.policy import eligibility, free_seat


def enroll(event, time, state):
    order = event["order"]
    if order in state["queue"]:
        return "WAIT_DUPLICATE"
    if order in state["tickets"] or order in state["holds"]:
        return "ORDER_ACTIVE"
    entry = {key: event[key] for key in ("order", "trip", "tier", "group", "row", "id")}
    code = eligibility(event, time, state)
    state["queue"][order] = dict(
        entry, queued_at=time, state="REJECTED" if code else "WAITING", code=code
    )
    return code


def advance(time, state):
    # 入队顺序与回放时间和来源行一致。
    queue = (item for item in state["queue"].values() if item["state"] == "WAITING")
    for item in queue:
        order = item["order"]
        if order in state["tickets"] or order in state["holds"]:
            item.update(state="REJECTED", code="ORDER_ACTIVE")
        elif eligibility(item, time, state):
            item.update(state="CLOSED", code="BOOKING_CLOSED")
        elif free_seat(item, state):
            proof = {
                key: item[key] for key in ("order", "trip", "tier", "group", "row")
            }
            proof.update(ticket=item["id"], time=time)
            state["remaining"][item["trip"], item["tier"]] -= 1
            state["tickets"][order] = proof
            item.update(state="PROMOTED", promoted_at=time)
            state["promoted"].append(dict(item))


def outcome(state, as_of):
    advance(as_of, state)
    return {
        "queue": list(state["queue"].values()),
        "promoted": state["promoted"],
        "counts": {
            status.lower(): sum(
                item["state"] == status for item in state["queue"].values()
            )
            for status in ("PROMOTED", "WAITING", "REJECTED", "CLOSED")
        },
    }
