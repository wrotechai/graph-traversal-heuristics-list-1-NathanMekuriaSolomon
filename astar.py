import heapq
import itertools
from utils import haversine


def astar(graph, stops, start_ids, goal_ids, start_time: int, criterion: str):
    stop_map = stops.set_index("stop_id")
    goal_set = set(goal_ids)
    counter = itertools.count()

    def h(node_id):
        if criterion == "t" and node_id in stop_map.index:
            a = stop_map.loc[node_id]
            candidates = [
                haversine(a["stop_lat"], a["stop_lon"],
                          stop_map.loc[g]["stop_lat"], stop_map.loc[g]["stop_lon"])
                for g in goal_set if g in stop_map.index
            ]
            return min(candidates) / 12.5 if candidates else 0
        return 0

    pq = []
    # For criterion 't': best[(stop, route)] = lowest cost (arrival time) seen
    # For criterion 'p': best[(stop, route, transfers)] = lowest clock time seen.
    #   Two states with equal (stop, route, transfers) but different clock times
    #   are distinct — the earlier clock enables earlier onward connections.
    best = {}
    parent = {}

    for s in start_ids:
        g0 = start_time if criterion == "t" else 0
        f0 = (g0 + h(s)) if criterion == "t" else (0, start_time)
        heapq.heappush(pq, (f0, next(counter), g0, s, start_time, None))
        if criterion == "t":
            best[(s, None)] = g0
        else:
            best[(s, None, 0)] = start_time

    while pq:
        f, _, g, u, t, last_r = heapq.heappop(pq)

        if criterion == "t":
            if g > best.get((u, last_r), float("inf")):
                continue
        else:
            if t > best.get((u, last_r, g), float("inf")):
                continue

        if u in goal_set:
            return parent, (u, g, last_r), t

        for e in graph.get(u, []):
            if e["type"] == "trip":
                if e["dep"] < t:
                    continue
                nt = e["arr"]
                nr = e.get("route")
                if criterion == "t":
                    ng = nt
                else:
                    # First boarding (last_r is None) is free; switching lines costs +1
                    ng = g + (1 if (last_r is not None and nr != last_r) else 0)
            else:
                # Platform walk — clock advances, route context preserved (no reset)
                nt = t + e["time"]
                ng = g
                nr = last_r

            if criterion == "t":
                state_key = (e["to"], nr)
                if ng < best.get(state_key, float("inf")):
                    best[state_key] = ng
                    parent[(e["to"], ng, nr)] = (u, g, last_r, e)
                    nf = ng + h(e["to"])
                    heapq.heappush(pq, (nf, next(counter), ng, e["to"], nt, nr))
            else:
                state_key = (e["to"], nr, ng)
                if nt < best.get(state_key, float("inf")):
                    best[state_key] = nt
                    parent[(e["to"], ng, nr)] = (u, g, last_r, e)
                    nf = (ng, nt)
                    heapq.heappush(pq, (nf, next(counter), ng, e["to"], nt, nr))

    return None, None, None


def reconstruct_path(parent, last_state):
    if not parent or not last_state:
        return []
    path = []
    curr = last_state
    while curr in parent:
        p_u, p_g, p_r, e = parent[curr]
        path.append((p_u, curr[0], e))
        curr = (p_u, p_g, p_r)
    path.reverse()
    return path