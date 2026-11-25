from app.quality import instant, token


def window(raw):
    opened, close, refund, departure = (
        instant(raw[key]) for key in ("open", "close", "refund_until", "departure")
    )
    if not opened < close <= departure or not opened <= refund <= departure:
        raise ValueError
    origin, destination = token(raw["origin"]), token(raw["destination"])
    if origin == destination:
        raise ValueError
    return {
        "id": token(raw["id"]),
        "origin": origin,
        "destination": destination,
        "open": opened,
        "close": close,
        "refund_until": refund,
        "departure": departure,
    }


def bookable(sailing, time):
    return sailing["open"] <= time < sailing["close"]
