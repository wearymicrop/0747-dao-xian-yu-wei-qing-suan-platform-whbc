from app.quality import instant, token

TYPES = {"pay", "hold", "wait", "refund", "swap"}


def event_fields(raw):
    event = {
        key: token(raw[key]) for key in ("id", "type", "order", "trip", "tier", "group")
    }
    kind = event["type"]
    if kind not in TYPES:
        raise ValueError
    event["time"] = instant(raw["time"])
    event["received"] = instant(raw.get("received", raw["time"]))
    if event["received"] < event["time"]:
        raise ValueError
    if kind == "pay":
        event["payment"] = token(raw["payment"])
    if kind in {"swap", "refund"}:
        event["ticket"] = token(raw["ticket"])
    if kind == "hold":
        event["expires"] = instant(raw["expires"])
        if (
            event["expires"] <= event["time"]
            or event["expires"] - event["time"] > 86400
        ):
            raise ValueError
    if kind == "swap":
        event["to_trip"], event["to_tier"] = (
            token(raw["to_trip"]),
            token(raw["to_tier"]),
        )
    return event


def event_time(event):
    return event["received"] if event["type"] == "refund" else event["time"]
