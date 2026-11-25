from app.errors import BusinessError


def approval(result):
    if result["reconcile"]["status"] != "MATCHED":
        raise BusinessError("UNBALANCED", "船班余位尚未对平", 409)
    isolated = sum(
        len(result[key]["isolated"])
        for key in ("sailings", "seats", "orders", "transfers")
    )
    return {
        "status": "NOTED" if isolated else "CLEARED",
        "isolated": isolated,
        "decision": "已留档，异常待航务复核" if isolated else "准予留档",
    }
