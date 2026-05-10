from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Edge, Node, RouteQueryHistory
from app.services import find_shortest_path

api = Blueprint("api", __name__)


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


def clean_name(value):
    if not isinstance(value, str):
        return None
    name = value.strip()
    return name or None


def get_json_body():
    return request.get_json(silent=True) or {}


@api.post("/nodes")
def create_node():
    data = get_json_body()
    name = clean_name(data.get("name"))

    if not name:
        return error_response("Name is required", 400)

    if Node.query.filter_by(name=name).first():
        return error_response(f"Node '{name}' already exists", 400)

    node = Node(name=name)
    db.session.add(node)
    db.session.commit()

    return jsonify(node.to_dict()), 201


@api.get("/nodes")
def list_nodes():
    nodes = Node.query.order_by(Node.id.asc()).all()
    return jsonify([node.to_dict() for node in nodes])


@api.delete("/nodes/<int:node_id>")
def delete_node(node_id):
    node = db.session.get(Node, node_id)
    if not node:
        return error_response("Node not found", 404)

    db.session.delete(node)
    db.session.commit()
    return "", 204


@api.post("/edges")
def create_edge():
    data = get_json_body()
    source_name = clean_name(data.get("source"))
    destination_name = clean_name(data.get("destination"))
    latency = data.get("latency")

    if not source_name or not destination_name:
        return error_response("Source and destination are required", 400)

    try:
        latency = float(latency)
    except (TypeError, ValueError):
        return error_response("Latency must be a positive number", 400)

    if latency <= 0:
        return error_response("Latency must be greater than 0", 400)

    source = Node.query.filter_by(name=source_name).first()
    destination = Node.query.filter_by(name=destination_name).first()
    if not source or not destination:
        return error_response("Source or destination node not found", 400)

    if Edge.query.filter_by(source_id=source.id, destination_id=destination.id).first():
        return error_response(f"Edge from {source_name} to {destination_name} already exists", 400)

    edge = Edge(source_node=source, destination_node=destination, latency=latency)
    db.session.add(edge)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("Could not create edge", 400)

    return jsonify(edge.to_dict()), 201


@api.get("/edges")
def list_edges():
    edges = Edge.query.order_by(Edge.id.asc()).all()
    return jsonify([edge.to_dict() for edge in edges])


@api.delete("/edges/<int:edge_id>")
def delete_edge(edge_id):
    edge = db.session.get(Edge, edge_id)
    if not edge:
        return error_response("Edge not found", 404)

    db.session.delete(edge)
    db.session.commit()
    return "", 204


@api.post("/routes/shortest")
def shortest_route():
    data = get_json_body()
    source_name = clean_name(data.get("source"))
    destination_name = clean_name(data.get("destination"))

    if not source_name or not destination_name:
        return error_response("Source and destination are required", 400)

    source = Node.query.filter_by(name=source_name).first()
    destination = Node.query.filter_by(name=destination_name).first()
    if not source or not destination:
        return error_response("Invalid or non-existent nodes", 400)

    result = find_shortest_path(source, destination)
    if not result:
        return error_response(f"No path exists between {source_name} and {destination_name}", 404)

    history = RouteQueryHistory(
        source_node=source,
        destination_node=destination,
        total_latency=result["total_latency"],
        path=result["path"],
    )
    db.session.add(history)
    db.session.commit()

    return jsonify(result)


@api.get("/routes/history")
def route_history():
    query = RouteQueryHistory.query

    source_name = clean_name(request.args.get("source"))
    destination_name = clean_name(request.args.get("destination"))
    limit = request.args.get("limit")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    if source_name:
        source = Node.query.filter_by(name=source_name).first()
        if not source:
            return jsonify([])
        query = query.filter(RouteQueryHistory.source_id == source.id)

    if destination_name:
        destination = Node.query.filter_by(name=destination_name).first()
        if not destination:
            return jsonify([])
        query = query.filter(RouteQueryHistory.destination_id == destination.id)

    if date_from:
        parsed = parse_datetime_param(date_from, "date_from")
        if isinstance(parsed, tuple):
            return parsed
        query = query.filter(RouteQueryHistory.created_at >= parsed)

    if date_to:
        parsed = parse_datetime_param(date_to, "date_to")
        if isinstance(parsed, tuple):
            return parsed
        query = query.filter(RouteQueryHistory.created_at <= parsed)

    query = query.order_by(RouteQueryHistory.created_at.desc(), RouteQueryHistory.id.desc())

    if limit:
        try:
            limit_value = int(limit)
        except ValueError:
            return error_response("Limit must be a positive integer", 400)
        if limit_value <= 0:
            return error_response("Limit must be a positive integer", 400)
        query = query.limit(limit_value)

    return jsonify([item.to_dict() for item in query.all()])


def parse_datetime_param(value, field_name):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return error_response(f"{field_name} must be an ISO 8601 datetime", 400)
