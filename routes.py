import logging
from itertools import combinations
from geopy.distance import geodesic
from functools import lru_cache

# Get the logger specific to this module
logger = logging.getLogger('routes')

@lru_cache(maxsize=None)
def calculate_distance(point1, point2):
    """
    Calculate the geodesic distance between two points using latitude and longitude.
    The result is cached for repeated calls to improve performance.
    """
    try:
        distance = geodesic(point1, point2).km
        logger.debug(f"Calculated distance between {point1} and {point2}: {distance} km")
        return distance
    except Exception as e:
        logger.error(f"Error calculating distance between {point1} and {point2}: {e}")
        return float('inf')

def calculate_symmetric_distances(relatives, tarjan_home):
    """
    Calculate the symmetric distance matrix for all relatives and Tarjan's home.
    """
    distances = {}

    # Precompute distances between relatives
    for rel1, rel2 in combinations(relatives, 2):
        distance = calculate_distance(
            (rel1["latitude"], rel1["longitude"]),
            (rel2["latitude"], rel2["longitude"])
        )
        distances[(rel1["name"], rel2["name"])] = distance
        distances[(rel2["name"], rel1["name"])] = distance
        logger.debug(f"Distance between {rel1['name']} and {rel2['name']}: {distance} km")

    # Precompute distances from Tarjan's home to all relatives
    for relative in relatives:
        distance_to_home = calculate_distance(
            (tarjan_home["latitude"], tarjan_home["longitude"]),
            (relative["latitude"], relative["longitude"])
        )
        distances[(tarjan_home["name"], relative["name"])] = distance_to_home
        distances[(relative["name"], tarjan_home["name"])] = distance_to_home
        logger.debug(f"Distance from {tarjan_home['name']} to {relative['name']}: {distance_to_home} km")

    logger.info("Symmetric distances between relatives and Tarjan's home have been calculated.")
    return distances

def find_shortest_route(relatives, distances, tarjan_home_name):
    """
    Find the shortest route starting from Tarjan's home and visiting all relatives.
    """
    if not relatives:
        logger.warning("No relatives provided. Returning empty route.")
        return {"route": [], "distance": 0}

    if len(relatives) == 1:
        relative = relatives[0]
        distance = distances[(tarjan_home_name, relative["name"])] + distances[(relative["name"], tarjan_home_name)]
        logger.info(f"Single relative provided. Route: {tarjan_home_name} -> {relative['name']} with distance {distance} km.")
        return {"route": [tarjan_home_name, relative["name"]], "distance": distance}

    relative_names = [rel["name"] for rel in relatives]
    n = len(relative_names)

    # Dynamic Programming for TSP solution
    dp = [[float('inf')] * (1 << n) for _ in range(n)]
    parent = [[-1] * (1 << n) for _ in range(n)]

    for i in range(n):
        dp[i][1 << i] = distances[(tarjan_home_name, relative_names[i])]
        logger.debug(f"Initial DP setup for {relative_names[i]} with distance {dp[i][1 << i]}")

    for mask in range(1, 1 << n):
        for u in range(n):
            if mask & (1 << u):
                for v in range(n):
                    if not mask & (1 << v):
                        new_mask = mask | (1 << v)
                        new_distance = dp[u][mask] + distances[(relative_names[u], relative_names[v])]
                        if new_distance < dp[v][new_mask]:
                            dp[v][new_mask] = new_distance
                            parent[v][new_mask] = u
                            logger.debug(f"Updated DP for {relative_names[v]} with new distance {new_distance}")

    min_distance = float('inf')
    last_node = -1
    final_mask = (1 << n) - 1

    for i in range(n):
        if dp[i][final_mask] < min_distance:
            min_distance = dp[i][final_mask]
            last_node = i

    route = []
    mask = final_mask
    while last_node != -1:
        route.append(relative_names[last_node])
        next_node = parent[last_node][mask]
        mask ^= (1 << last_node)
        last_node = next_node

    route.reverse()

    logger.info(f"Shortest route found: {tarjan_home_name} -> " + " -> ".join(route) + f" with total distance {min_distance} km.")
    return {"route": [tarjan_home_name] + route, "distance": min_distance}
