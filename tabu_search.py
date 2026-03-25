import itertools
from astar import astar, reconstruct_path

def _cost_of_tour(depot_ids, ordered_ids, graph, stops, start_time, criterion):
    full_path = []
    current_ids = list(depot_ids)
    current_time = start_time
    # Track route and g-cost across legs
    last_r = None
    last_g = 0 if criterion == "p" else start_time

    legs = list(ordered_ids) + [None] 
    for target_id in legs:
        goal_ids = list(depot_ids) if target_id is None else [target_id]
        
        # We must use a modified call or handle the fact that astar 
        # starts fresh each leg. For TSP, we reset g but keep the route.
        parent, last_state, arr = astar(
            graph, stops, current_ids, goal_ids, current_time, criterion
        )
        
        if arr is None:
            return float("inf"), []
            
        seg = reconstruct_path(parent, last_state)
        full_path.extend(seg)
        
        # Update for next leg: last_state is (u, g, nr)
        current_ids = [last_state[0]]
        current_time = arr
        # last_r = last_state[2] # Optional: carry route context to next leg

    return current_time, full_path

def _greedy_init(depot_ids, visit_ids, graph, stops, start_time, criterion):
    remaining = list(visit_ids)
    current_ids = list(depot_ids)
    current_time = start_time
    order = []

    while remaining:
        best_arr = float("inf")
        best_target = None
        for target in remaining:
            _, _, arr = astar(graph, stops, current_ids, [target],
                              current_time, criterion)
            if arr is not None and arr < best_arr:
                best_arr = arr
                best_target = target

        if best_target is None: break 

        order.append(best_target)
        current_ids = [best_target]
        current_time = best_arr
        remaining.remove(best_target)

    return order

def tabu_search(depot_ids, visit_ids, graph, stops, start_time, criterion,
                max_iter=50, tabu_tenure=7):
    n = len(visit_ids)
    if n == 0: return start_time, []
    
    current_order = _greedy_init(depot_ids, list(visit_ids), graph, stops,
                                 start_time, criterion)
    if not current_order: return float("inf"), []

    current_cost, current_path = _cost_of_tour(
        depot_ids, current_order, graph, stops, start_time, criterion
    )
    
    best_order = list(current_order)
    best_cost = current_cost
    best_path = current_path
    tabu_list = {} 

    for iteration in range(max_iter):
        best_neighbour_cost = float("inf")
        best_neighbour_order = None
        best_swap_key = None

        for i in range(n - 1):
            for j in range(i + 1, n):
                swap_key = (i, j)
                neighbour = (current_order[:i]
                             + list(reversed(current_order[i:j + 1]))
                             + current_order[j + 1:])

                cost, _ = _cost_of_tour(depot_ids, neighbour, graph, stops,
                                        start_time, criterion)

                not_tabu = tabu_list.get(swap_key, 0) <= iteration
                aspiration = cost < best_cost

                if (not_tabu or aspiration) and cost < best_neighbour_cost:
                    best_neighbour_cost = cost
                    best_neighbour_order = neighbour
                    best_swap_key = swap_key

        if best_neighbour_order is None: break 

        current_order = best_neighbour_order
        current_cost = best_neighbour_cost
        tabu_list[best_swap_key] = iteration + tabu_tenure

        if current_cost < best_cost:
            best_cost = current_cost
            best_order = list(current_order)
            _, best_path = _cost_of_tour(depot_ids, best_order, graph, stops,
                                         start_time, criterion)

    return best_cost, best_path