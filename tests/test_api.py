def add_node(client, name):
    return client.post("/nodes", json={"name": name})


def add_edge(client, source, destination, latency):
    return client.post(
        "/edges",
        json={"source": source, "destination": destination, "latency": latency},
    )


def test_create_nodes_and_edges(client):
    response = add_node(client, "ServerA")
    assert response.status_code == 201
    assert response.get_json()["name"] == "ServerA"

    assert add_node(client, "ServerA").status_code == 400
    assert add_node(client, "").status_code == 400

    add_node(client, "ServerB")
    response = add_edge(client, "ServerA", "ServerB", 12.5)
    assert response.status_code == 201
    assert response.get_json()["latency"] == 12.5

    assert add_edge(client, "ServerA", "ServerB", 12.5).status_code == 400
    assert add_edge(client, "ServerA", "ServerC", 12.5).status_code == 400
    assert add_edge(client, "ServerA", "ServerB", 0).status_code == 400


def test_shortest_route_and_history(client):
    for name in ["ServerA", "ServerB", "ServerC", "ServerD"]:
        add_node(client, name)

    add_edge(client, "ServerA", "ServerB", 12.5)
    add_edge(client, "ServerB", "ServerD", 10.9)
    add_edge(client, "ServerA", "ServerC", 50)
    add_edge(client, "ServerC", "ServerD", 1)

    response = client.post(
        "/routes/shortest",
        json={"source": "ServerA", "destination": "ServerD"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "total_latency": 23.4,
        "path": ["ServerA", "ServerB", "ServerD"],
    }

    history = client.get("/routes/history?source=ServerA&destination=ServerD&limit=1")
    assert history.status_code == 200
    body = history.get_json()
    assert len(body) == 1
    assert body[0]["total_latency"] == 23.4
    assert body[0]["path"] == ["ServerA", "ServerB", "ServerD"]


def test_shortest_route_no_path(client):
    add_node(client, "ServerA")
    add_node(client, "ServerD")

    response = client.post(
        "/routes/shortest",
        json={"source": "ServerA", "destination": "ServerD"},
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "No path exists between ServerA and ServerD"


def test_list_and_delete_optional_endpoints(client):
    add_node(client, "ServerA")
    add_node(client, "ServerB")
    add_edge(client, "ServerA", "ServerB", 3.5)

    assert len(client.get("/nodes").get_json()) == 2
    assert len(client.get("/edges").get_json()) == 1

    assert client.delete("/edges/1").status_code == 204
    assert client.delete("/nodes/1").status_code == 204
