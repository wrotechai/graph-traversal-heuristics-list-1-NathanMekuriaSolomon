import math


def time_to_seconds(t: str) -> int:
    """Convert HH:MM or HH:MM:SS string to seconds since midnight."""
    parts = t.strip().split(":")
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) > 2 else 0
    return h * 3600 + m * 60 + s


def seconds_to_time(sec: int) -> str:
    """Convert seconds since midnight to HH:MM string."""
    sec = int(sec)
    h = sec // 3600
    m = (sec % 3600) // 60
    return f"{h:02}:{m:02}"


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in metres between two lat/lon points."""
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))