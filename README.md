# Network Route Optimization API

Flask API for storing network nodes, directed latency edges, shortest-route queries, and route query history.

## Folder Structure

```text
network_route/
├── app/
│   ├── __init__.py        # Flask application factory and app setup
│   ├── extensions.py      # SQLAlchemy extension instance
│   ├── models.py          # Database schema/models
│   ├── routes.py          # API routes and validation
│   └── services.py        # Dijkstra shortest-path logic
├── tests/
│   ├── conftest.py        # Test app/database setup
│   └── test_api.py        # API endpoint tests
├── docker-compose.yml     # Easy PostgreSQL setup for local testing
├── .env.example           # Example environment variables
├── README.md
├── requirements.txt       # Python dependencies
└── run.py                 # Local app entrypoint
```

## Database Schema

### `nodes`

Stores each network node/server.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer | Primary key |
| `name` | String | Required, unique |
| `created_at` | DateTime | UTC creation timestamp |

### `edges`

Stores directed network connections between nodes.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer | Primary key |
| `source_id` | Integer | Foreign key to `nodes.id` |
| `destination_id` | Integer | Foreign key to `nodes.id` |
| `latency` | Float | Required, must be greater than `0` |
| `created_at` | DateTime | UTC creation timestamp |

Unique constraint: one edge per source and destination pair.

### `route_query_history`

Stores successful shortest-route lookups.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer | Primary key |
| `source_id` | Integer | Foreign key to `nodes.id` |
| `destination_id` | Integer | Foreign key to `nodes.id` |
| `total_latency` | Float | Shortest total latency |
| `path` | JSON | Ordered list of node names |
| `created_at` | DateTime | UTC query timestamp |

## Setup

### Option 1: Recommended Setup With Docker PostgreSQL

Requirements:

- Python 3
- Docker

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file from the example:

```bash
cp .env.example .env
```

The default `.env` works with `docker-compose.yml`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:55432/network_route
AUTO_CREATE_TABLES=true
FLASK_DEBUG=1
```

The Docker database runs inside the container on port `5432`, but it is exposed on your laptop as port `55432`. This avoids conflicts if you already have local PostgreSQL using port `5432`.

Start PostgreSQL in Docker:

```bash
docker compose up -d postgres
```

Run the API:

```bash
python run.py
```

Tables are created automatically on startup using `db.create_all()`.

The API runs at:

```text
http://127.0.0.1:5000
```

To stop the database:

```bash
docker compose down
```

To stop the database and delete all stored data:

```bash
docker compose down -v
```

## API Endpoints

### Add Node

```http
POST /nodes
```

```json
{
  "name": "ServerA"
}
```

Response:

```json
{
  "id": 1,
  "name": "ServerA"
}
```

### Add Edge

```http
POST /edges
```

```json
{
  "source": "ServerA",
  "destination": "ServerB",
  "latency": 12.5
}
```

### Get Shortest Route

```http
POST /routes/shortest
```

```json
{
  "source": "ServerA",
  "destination": "ServerD"
}
```

Path found:

```json
{
  "total_latency": 23.4,
  "path": ["ServerA", "ServerB", "ServerD"]
}
```

No path:

```json
{
  "error": "No path exists between ServerA and ServerD"
}
```

### Get Route Query History

```http
GET /routes/history
```

Optional query parameters:

| Parameter | Description |
| --- | --- |
| `source` | Filter by source node name |
| `destination` | Filter by destination node name |
| `limit` | Maximum number of records |
| `date_from` | ISO 8601 start datetime |
| `date_to` | ISO 8601 end datetime |

### Optional Endpoints

```http
GET /nodes
GET /edges
DELETE /nodes/{id}
DELETE /edges/{id}
```

## Example Flow

```bash
curl -X POST http://127.0.0.1:5000/nodes \
  -H "Content-Type: application/json" \
  -d '{"name":"ServerA"}'

curl -X POST http://127.0.0.1:5000/nodes \
  -H "Content-Type: application/json" \
  -d '{"name":"ServerB"}'

curl -X POST http://127.0.0.1:5000/edges \
  -H "Content-Type: application/json" \
  -d '{"source":"ServerA","destination":"ServerB","latency":12.5}'

curl -X POST http://127.0.0.1:5000/routes/shortest \
  -H "Content-Type: application/json" \
  -d '{"source":"ServerA","destination":"ServerB"}'
```

## Tests

The test files are inside the `tests/` folder:

```text
tests/
├── conftest.py
└── test_api.py
```

After activating the virtual environment and installing dependencies, run:

```bash
python3 -m pytest tests -q
```

The tests use an in-memory SQLite database, so PostgreSQL does not need to be running for tests.

Expected output:

```bash
4 passed
```
