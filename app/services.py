import heapq
from collections import defaultdict

from app.models import Edge


def find_shortest_path(source_node, destination_node):
    graph = defaultdict(list)
    edges = Edge.query.all()

    for edge in edges:
        graph[edge.source_id].append((edge.destination_id, edge.latency, edge.destination_node.name))

    distances = {source_node.id: 0.0}
    previous = {}
    names = {source_node.id: source_node.name, destination_node.id: destination_node.name}
    queue = [(0.0, source_node.id)]
    visited = set()

    while queue:
        current_distance, current_id = heapq.heappop(queue)
        if current_id in visited:
            continue

        visited.add(current_id)
        if current_id == destination_node.id:
            break

        for neighbor_id, latency, neighbor_name in graph[current_id]:
            if neighbor_id in visited:
                continue

            new_distance = current_distance + latency
            if new_distance < distances.get(neighbor_id, float("inf")):
                distances[neighbor_id] = new_distance
                previous[neighbor_id] = current_id
                names[neighbor_id] = neighbor_name
                heapq.heappush(queue, (new_distance, neighbor_id))

    if destination_node.id not in distances:
        return None

    path_ids = []
    current_id = destination_node.id
    while current_id != source_node.id:
        path_ids.append(current_id)
        current_id = previous[current_id]
    path_ids.append(source_node.id)
    path_ids.reverse()

    return {
        "total_latency": round(distances[destination_node.id], 2),
        "path": [names[node_id] for node_id in path_ids],
    }
