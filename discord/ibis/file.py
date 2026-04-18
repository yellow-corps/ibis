from datetime import datetime


def unique(suffix: str) -> str:
    date = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{date}.{suffix}"
