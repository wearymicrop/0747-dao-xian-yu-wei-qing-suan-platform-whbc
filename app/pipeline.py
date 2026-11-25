from app.modules.m1_sailings.service import schedule
from app.modules.m2_seats.service import capacity
from app.modules.m3_orders.service import collect
from app.modules.m4_transfers.service import replay
from app.modules.m6_reconcile.service import reconcile


def calculate(data):
    sailings = schedule(data)
    seats = capacity(data, sailings)
    orders = collect(data, sailings["as_of"])
    transfers, waitlist = replay(sailings, seats, orders)
    return {
        "sailings": sailings,
        "seats": seats,
        "orders": orders,
        "transfers": transfers,
        "waitlist": waitlist,
        "reconcile": reconcile(seats, orders, transfers),
    }
