import os
import pandas as pd
from datetime import datetime


def build_graph(gtfs_path: str, date_str: str):
    # Load GTFS.
    # Build graph.
    stops      = pd.read_csv(os.path.join(gtfs_path, "stops.txt"))
    stop_times = pd.read_csv(os.path.join(gtfs_path, "stop_times.txt"))
    trips      = pd.read_csv(os.path.join(gtfs_path, "trips.txt"))
    calendar   = pd.read_csv(os.path.join(gtfs_path, "calendar.txt"))
    routes     = pd.read_csv(os.path.join(gtfs_path, "routes.txt"))

    # Map route_id -> human-readable short name (e.g. 'D6', 'D1')
    route_id_to_name = dict(zip(routes["route_id"], routes["route_short_name"]))

    # 1. Filter services
    date_obj  = datetime.strptime(date_str, "%Y-%m-%d")
    day_name  = date_obj.strftime("%A").lower()   # e.g. 'wednesday'
    date_int  = int(date_str.replace("-", ""))    # e.g. 20260304

    active_services = calendar[
        (calendar[day_name] == 1) &
        (calendar["start_date"] <= date_int) &
        (calendar["end_date"]   >= date_int)
    ]["service_id"].tolist()

    valid_trips  = trips[trips["service_id"].isin(active_services)]
    trip_to_route = dict(zip(valid_trips["trip_id"], valid_trips["route_id"]))

    # 2. Filter active trips
    st = stop_times[stop_times["trip_id"].isin(trip_to_route)].copy()

    def _to_sec(t: str) -> int:
        h, m, s = map(int, t.strip().split(":"))
        return h * 3600 + m * 60 + s

    st["dep_s"] = st["departure_time"].apply(_to_sec)
    st["arr_s"] = st["arrival_time"].apply(_to_sec)
    st = st.sort_values(["trip_id", "stop_sequence"])

    # 3. Build trip edges
    graph: dict = {}

    for trip_id, group in st.groupby("trip_id"):
        nodes = group.to_dict("records")
        route = route_id_to_name.get(trip_to_route[trip_id], trip_to_route[trip_id])
        for i in range(len(nodes) - 1):
            u = nodes[i]["stop_id"]
            v = nodes[i + 1]["stop_id"]
            graph.setdefault(u, []).append({
                "to":    v,
                "type":  "trip",
                "dep":   nodes[i]["dep_s"],
                "arr":   nodes[i + 1]["arr_s"],
                "route": route,
            })

    # 4. Platform
    for _, grp in stops.groupby("stop_name"):
        ids = grp["stop_id"].tolist()
        if len(ids) < 2:
            continue
        for s1 in ids:
            for s2 in ids:
                if s1 != s2:
                    graph.setdefault(s1, []).append({
                        "to":    s2,
                        "type":  "transfer",
                        "time":  120,   # 2 minutes in seconds
                        "route": "WALK",
                    })

    return graph, stops