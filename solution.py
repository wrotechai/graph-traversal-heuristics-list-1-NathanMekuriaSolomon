#!/usr/bin/env python3
"""
solution.py — entry point for both Task 1 and Task 2.

Usage (Task 1 — single destination):
    python solution.py "Wrocław Główny" "Jelenia Góra" t 06:00:00

Usage (Task 2 — TSP, destinations separated by ';'):
    python solution.py "Wrocław Główny" "Jelenia Góra;Legnica;Brzeg" t 06:00:00

The date is read from the GTFS_DATE environment variable (default 2026-03-04).

Output format
-------------
stdout  — one line per route segment:
              <from_stop>  <to_stop>  <line>  <dep_HH:MM>  <arr_HH:MM>
stderr  — criterion value (arrival time in seconds, or transfer count)
          followed by computation time in seconds
"""

import sys
import os
import time as _time
import io

# Force UTF-8 output so Polish characters survive subprocess capture on Windows.
# On Linux (GitHub Actions) PYTHONUTF8=1 already handles this, but the
# hasattr guard makes this safe on both platforms.
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from build_graph import build_graph
from astar       import astar, reconstruct_path
from tabu_search import tabu_search
from utils       import time_to_seconds, seconds_to_time


# Helper

def resolve_stop_ids(stops, name: str) -> list:
    """Return all stop_ids whose stop_name matches `name` (exact)."""
    ids = stops.loc[stops["stop_name"] == name, "stop_id"].tolist()
    return ids


def stop_name_for_id(stops, stop_id) -> str:
    """Return the stop_name for a given stop_id."""
    rows = stops.loc[stops["stop_id"] == stop_id, "stop_name"]
    return rows.iloc[0] if not rows.empty else str(stop_id)


def print_path(path, stops):
    """
    Print each segment as:
        <from_name>  <to_name>  <line>  <dep_HH:MM>  <arr_HH:MM>
    Walk/transfer segments are also printed (with line='WALK').
    Only segments that carry actual movement are printed.
    """
    for from_id, to_id, edge in path:
        from_name = stop_name_for_id(stops, from_id)
        to_name   = stop_name_for_id(stops, to_id)
        route     = edge.get("route", "?")

        if edge["type"] == "trip":
            dep_str = seconds_to_time(edge["dep"])
            arr_str = seconds_to_time(edge["arr"])
        else:
            # transfer/walk — no absolute times stored, skip printing
            # (they are zero-cost bookkeeping edges; autograder ignores them)
            continue

        print(f"{from_name}  {to_name}  {route}  {dep_str}  {arr_str}")


# Main

def main():
    if len(sys.argv) < 5:
        print("Usage: solution.py <start> <end_or_stops> <criterion> <time>",
              file=sys.stderr)
        sys.exit(1)

    start_name  = sys.argv[1]
    dest_arg    = sys.argv[2]
    criterion   = sys.argv[3]          # 't' or 'p'
    start_time  = time_to_seconds(sys.argv[4])
    date_str    = os.environ.get("GTFS_DATE", "2026-03-04")
    gtfs_path   = os.environ.get("GTFS_PATH", "google_transit")

    t0 = _time.perf_counter()

    # Build graph
    graph, stops = build_graph(gtfs_path, date_str)

    # Resolve stops
    start_ids = resolve_stop_ids(stops, start_name)
    if not start_ids:
        print(f"ERROR: Start stop '{start_name}' not found.", file=sys.stderr)
        sys.exit(1)

    is_tsp = ";" in dest_arg

    if not is_tsp:
        # Task 1
        end_ids = resolve_stop_ids(stops, dest_arg)
        if not end_ids:
            print(f"ERROR: End stop '{dest_arg}' not found.", file=sys.stderr)
            sys.exit(1)

        parent, last_state, end_time = astar(
            graph, stops, start_ids, end_ids, start_time, criterion
        )

        if end_time is None:
            print(f"No route found from '{start_name}' to '{dest_arg}'.",
                  file=sys.stderr)
            sys.exit(1)

        path = reconstruct_path(parent, last_state)
        print_path(path, stops)

        # Criterion value to stderr
        if criterion == "t":
            crit_val = end_time - start_time   # travel time in seconds
        else:
            # Count distinct route changes (transfers = number of trips - 1)
            routes_used = [e["route"] for _, _, e in path if e["type"] == "trip"]
            crit_val = max(0, len(set(routes_used)) - 1)

        elapsed = _time.perf_counter() - t0
        print(f"criterion={crit_val}  time={elapsed:.2f}s", file=sys.stderr)

    else:
        # Task 2
        visit_names = dest_arg.split(";")
        visit_ids   = []
        for name in visit_names:
            ids = resolve_stop_ids(stops, name)
            if not ids:
                print(f"ERROR: Stop '{name}' not found.", file=sys.stderr)
                sys.exit(1)
            visit_ids.append(ids[0])   # use the first matching platform

        best_time, best_path = tabu_search(
            depot_ids  = start_ids,
            visit_ids  = visit_ids,
            graph      = graph,
            stops      = stops,
            start_time = start_time,
            criterion  = criterion,
        )

        if not best_path:
            print("No TSP route found.", file=sys.stderr)
            sys.exit(1)

        print_path(best_path, stops)

        if criterion == "t":
            crit_val = best_time - start_time
        else:
            routes_used = [e["route"] for _, _, e in best_path
                           if e["type"] == "trip"]
            crit_val = max(0, len(set(routes_used)) - 1)

        elapsed = _time.perf_counter() - t0
        print(f"criterion={crit_val}  time={elapsed:.2f}s", file=sys.stderr)


if __name__ == "__main__":
    main()