from datetime import datetime, timezone

from app.extensions import db


class Node(db.Model):
    __tablename__ = "nodes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    outgoing_edges = db.relationship(
        "Edge",
        foreign_keys="Edge.source_id",
        cascade="all, delete-orphan",
        back_populates="source_node",
    )
    incoming_edges = db.relationship(
        "Edge",
        foreign_keys="Edge.destination_id",
        cascade="all, delete-orphan",
        back_populates="destination_node",
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Edge(db.Model):
    __tablename__ = "edges"
    __table_args__ = (
        db.UniqueConstraint("source_id", "destination_id", name="uq_edge_source_destination"),
        db.CheckConstraint("latency > 0", name="ck_edge_latency_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey("nodes.id"), nullable=False, index=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("nodes.id"), nullable=False, index=True)
    latency = db.Column(db.Float, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    source_node = db.relationship("Node", foreign_keys=[source_id], back_populates="outgoing_edges")
    destination_node = db.relationship(
        "Node",
        foreign_keys=[destination_id],
        back_populates="incoming_edges",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source_node.name,
            "destination": self.destination_node.name,
            "latency": self.latency,
        }


class RouteQueryHistory(db.Model):
    __tablename__ = "route_query_history"

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey("nodes.id"), nullable=False, index=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("nodes.id"), nullable=False, index=True)
    total_latency = db.Column(db.Float, nullable=False)
    path = db.Column(db.JSON, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    source_node = db.relationship("Node", foreign_keys=[source_id])
    destination_node = db.relationship("Node", foreign_keys=[destination_id])

    def to_dict(self):
        created_at = self.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        return {
            "id": self.id,
            "source": self.source_node.name,
            "destination": self.destination_node.name,
            "total_latency": self.total_latency,
            "path": self.path,
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
        }
