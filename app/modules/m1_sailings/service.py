from collections import defaultdict

from app.errors import BusinessError
from app.modules.m1_sailings.windows import bookable, window
from app.quality import instant, issue, rows


def schedule(data):
    try:
        as_of = instant(data.get("as_of"))
    except (ValueError, TypeError) as error:
        raise BusinessError("BAD_CUTOFF", "清算时点须带时区并精确到秒") from error
    buckets, isolated = defaultdict(list), []
    for row, raw in rows(data, "sailings"):
        try:
            sailing = window(raw)
            buckets[sailing["id"]].append((row, raw, sailing))
        except (KeyError, ValueError, TypeError):
            isolated.append(issue("BAD_SAILING", row, raw))
    valid = {}
    for key, items in buckets.items():
        if len(items) != 1:
            isolated.extend(
                issue("SAILING_CONFLICT", row, raw) for row, raw, _ in items
            )
            continue
        row, _, item = items[0]
        valid[key] = dict(
            item,
            row=row,
            bookable=bookable(item, as_of),
            sailed=as_of >= item["departure"],
        )
    if not valid:
        raise BusinessError("NO_SAILING", "来源没有可用船班")
    return {"as_of": as_of, "sailings": valid, "isolated": isolated}
