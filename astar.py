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

    # pq: (f, tie, g, u, time, last_route)
    pq = []
    # best: (u, last_route) -> min_g
    best = {}
    parent = {}

    for s in start_ids:
        g0 = start_time if criterion == "t" else 0
        f0 = g0 + h(s)
        heapq.heappush(pq, (f0, next(counter), g0, s, start_time, None))
        best[(s, None)] = g0

    while pq:
        f, _, g, u, t, last_r = heapq.heappop(pq)

        if g > best.get((u, last_r), float("inf")):
            continue

        if u in goal_set:
            return parent, (u, g, last_r), t

        for e in graph.get(u, []):
            if e["type"] == "trip":
                if e["dep"] < t: continue
                
                nt = e["arr"]
                nr = e.get("route")
                # Increment if new
                ng = nt if criterion == "t" else (g + (1 if nr != last_r else 0))
            else:
                nt = t + e["time"]
                nr = last_r # Keep route
                ng = nt if criterion == "t" else g

            state = (e["to"], nr)
            if ng < best.get(state, float("inf")):
                best[state] = ng
                parent[(e["to"], ng, nr)] = (u, g, last_r, e)
                nf = ng + h(e["to"])
                heapq.heappush(pq, (nf, next(counter), ng, e["to"], nt, nr))

    return None, None, None

def reconstruct_path(parent, last_state):
    if not parent or not last_state: return []
    path = []
    curr = last_state # (u, g, route)
    while curr in parent:
        p_u, p_g, p_r, e = parent[curr]
        path.append((p_u, curr[0], e))
        curr = (p_u, p_g, p_r)
    path.reverse()
    return path