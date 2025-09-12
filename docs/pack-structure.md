# Pack Structure Guide

## Overview

This guide covers the technical structure and organization of Catalyst Knowledge Packs.

## Pack File Structure

### Basic Pack Structure

Each pack consists of YAML configuration files:

```
pack-name/
├── pack.yaml                    # Main pack configuration
├── tools/                       # Tool definitions (optional)
├── transforms/                  # Data transformations (optional)
├── guardrails.yaml              # Security patterns (optional)
├── README.md                    # Documentation
└── examples/                    # Usage examples
```

### Pack Metadata (pack.yaml)

```yaml
metadata:
  name: "my_integration"
  version: "1.0.0"
  description: "API integration pack"
  
connection:
  type: "rest"
  base_url: "${API_URL}"
  auth:
    method: "bearer"
    token: "${API_TOKEN}"

tools:
  get_data:
    type: "list"
    description: "Get data from API"
    endpoint: "/data"
    
    # NEW in v1.1.0: Optional LLM optimization
    llm_metadata:
      display_name: "📊 Get Data"
      usage_hint: "Use this to retrieve data from the API"
      complexity: "basic"
      examples:
        - scenario: "User wants to see available data"
          usage: "Call this tool first to explore what's available"
    
    # Parameters with optional constraints
    parameters:
      - name: "limit"
        type: "integer"
        description: "Maximum items to return"
        constraints:  # NEW in v1.1.0
          min: 1
          max: 1000
          examples: [10, 50, 100]
```

## Pack Categories

### Community Packs (`.example` suffix)
- Example packs for learning
- Open source licensing
- Community contributions

### Custom Packs
- User-created integrations
- Private use or sharing
- Any licensing model

## Environment Variables

All pack configurations support environment variable substitution:

```yaml
# In pack.yaml
host: "${DATABASE_HOST}"
password: "${DB_PASSWORD}"

# In .env file
DATABASE_HOST=localhost
DB_PASSWORD=secret123
```

## Tool Parameters

Define parameters for dynamic tool execution:

```yaml
tools:
  search_data:
    type: "query"
    description: "Search data by criteria" 
    sql: "SELECT * FROM table WHERE date > {since_date} LIMIT {limit}"
    parameters:
      - name: "since_date"
        type: "string"
        required: true
      - name: "limit"
        type: "integer"
        default: 100
```

## Response Transformation

Transform responses using multiple engines:

```yaml
tools:
  process_data:
    type: "query"
    sql: "SELECT * FROM users"
    transform:
      type: "jq"
      expression: '.[] | {id, name, active: .status == "active"}'
```

Supported transform engines:
- `jq` - JSON query language
- `python` - Python code execution  
- `javascript` - JavaScript transformation
- `template` - Jinja2 templates

## Validation

Packs are validated for:
- YAML syntax correctness
- Required metadata fields
- Tool parameter consistency
- Connection configuration validity