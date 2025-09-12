# Catalyst Builder

Tools for creating and validating Catalyst Knowledge Packs.

## Installation

```bash
pip install catalyst-builder
```

## What are Knowledge Packs?

Knowledge Packs are YAML configurations that define tools for integrating with external systems through the MCP (Model Context Protocol).

## What's New in v1.1.0

**LLM-Optimized Knowledge Packs** - New optional features to improve AI tool discovery and usage:

- **Smart Tool Metadata** - Display names, usage hints, complexity levels
- **Parameter Constraints** - Min/max values, examples, validation patterns  
- **Tool Prerequisites** - Define safe tool usage sequences
- **External Transforms** - Reference Python/JS files for better maintainability

All features are **100% backward compatible** - existing packs continue to work unchanged!

See the [LLM Optimization Guide](docs/LLM_OPTIMIZATION.md) for details.

## Pack Structure

```yaml
# pack.yaml
metadata:
  name: "my_integration" 
  version: "1.0.0"
  description: "Integration with external API"

connection:
  type: "rest"
  base_url: "${API_URL}"
  auth:
    method: "bearer"
    token: "${API_TOKEN}"

tools:
  list_items:
    type: "list"
    description: "Get list of items"
    endpoint: "/items"
    method: "GET"
```

## Supported Integration Types

- **REST API** - HTTP/HTTPS API integrations
- **Database** - SQL and NoSQL database connections
- **File System** - Local files, S3, Azure Blob, Google Cloud Storage  
- **SSH** - Remote system access
- **Message Queue** - RabbitMQ, Kafka, Redis Pub/Sub

## Tool Types

- `list` - Get arrays of data
- `details` - Get specific resource details
- `query` - Run database queries
- `search` - Search with parameters
- `execute` - Run commands or scripts

## Parameters

Define parameters for dynamic tools:

```yaml
tools:
  search_users:
    type: "query"
    sql: "SELECT * FROM users WHERE created_at > {since_date}"
    parameters:
      - name: "since_date"
        type: "string"
        required: true
```

## Data Transformation

Transform responses with jq, Python, JavaScript, or templates:

```yaml
tools:
  process_data:
    type: "query"
    sql: "SELECT id, name, status FROM users"
    transform:
      type: "jq"
      expression: '.[] | {id, name, active: .status == "active"}'
```

## Validation

```bash
python -c "from catalyst_pack_schemas.validator import PackValidator; print(PackValidator().validate_pack('path/to/pack'))"
```

## Environment Variables

Use environment variables for sensitive data:

```yaml
connection:
  host: "${DB_HOST}"
  auth:
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"
```

## Dependencies

Optional dependencies for specific integrations:

```bash
# Database connections
pip install asyncpg          # PostgreSQL
pip install aiomysql         # MySQL
pip install aiosqlite        # SQLite
pip install motor            # MongoDB
pip install redis            # Redis

# Cloud storage
pip install aioboto3         # AWS S3
pip install google-cloud-storage  # Google Cloud
pip install azure-storage-blob    # Azure Blob

# Other integrations
pip install aio-pika         # RabbitMQ
pip install aiokafka         # Apache Kafka
pip install asyncssh         # SSH connections
```

## Documentation

- [Integration Types](docs/integration-patterns.md) - Detailed integration patterns
- [Pack Structure](docs/pack-structure.md) - Pack organization guide  
- [Pack Development](docs/pack-development-guide.md) - Creation guide
- [Security](docs/security-guardrails.md) - Security patterns

## Examples

See `examples/` directory for sample packs demonstrating various integration patterns.