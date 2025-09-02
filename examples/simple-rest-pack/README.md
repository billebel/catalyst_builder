# Simple REST Pack Example

**A basic REST API integration demonstrating core Catalyst Knowledge Pack concepts**

## Overview

This example pack shows how to create a simple REST API integration using JSONPlaceholder, a free testing API. It demonstrates:

- Basic pack structure and metadata
- REST API connection configuration
- Three common tool types (list, details, search)
- Parameter definitions and validation
- Prompt templates for AI assistance
- Resource documentation links

## Quick Start

### 1. Environment Setup

Create a `.env` file in your project root:

```bash
# .env
API_BASE_URL=https://jsonplaceholder.typicode.com
# API_TOKEN is optional for this public API
API_TOKEN=your_token_here_if_needed
```

### 2. Validate the Pack

```bash
# Validate this example pack
python -m catalyst_packs.cli validate examples/simple-rest-pack

# Expected output: ✓ VALID simple_rest_example
```

### 3. Test API Connection

You can test the API endpoints directly:

```bash
# Test the base API
curl https://jsonplaceholder.typicode.com/posts?_limit=5

# Test specific post
curl https://jsonplaceholder.typicode.com/posts/1
```

## Pack Structure Explained

### Metadata Section

```yaml
metadata:
  name: "simple_rest_example"        # Unique pack identifier
  version: "1.0.0"                   # Semantic version
  description: "Simple REST API..."  # Clear description
  vendor: "Catalyst Examples"        # Organization name
  domain: "analytics"                # Business domain
  compatibility: "2.0.0"             # Minimum schema version
```

**Key Points:**
- `name` must be unique and match directory name
- `version` should follow semantic versioning (x.y.z)
- `domain` categorizes the pack's business purpose
- `vendor` identifies the organization or creator

### Connection Configuration

```yaml
connection:
  type: "rest"                       # Connection type
  base_url: "${API_BASE_URL}"        # Environment variable reference
  timeout: 30                        # Request timeout in seconds
  auth:                              # Authentication (optional)
    method: "bearer"                 # Auth method
    token: "${API_TOKEN}"            # Token from environment
  headers:                           # Default headers
    Accept: "application/json"
    User-Agent: "Catalyst-Example/1.0"
```

**Key Points:**
- Use environment variables for all configuration values
- `base_url` is the root URL for all API endpoints
- `timeout` prevents hanging requests
- Headers are sent with every request

### Tool Definitions

#### List Tool (Collection Operations)

```yaml
tools:
  list_posts:
    type: "list"                     # Tool type for collections
    description: "Retrieve blog posts..." # LLM-friendly description
    endpoint: "/posts"               # API endpoint (relative to base_url)
    method: "GET"                    # HTTP method
    parameters:                      # Input parameters
      - name: "limit"
        type: "integer"
        required: false              # Optional parameter
        default: 10                  # Default value
        min_value: 1                 # Validation constraint
        max_value: 100
        description: "Maximum number of posts to return"
```

**When to Use:** Getting lists of items, collections, or arrays.

#### Details Tool (Individual Items)

```yaml
  get_post:
    type: "details"                  # Tool type for individual items
    description: "Get specific blog post details..."
    endpoint: "/posts/{post_id}"     # Path parameter in URL
    method: "GET"
    parameters:
      - name: "post_id"              # Maps to {post_id} in endpoint
        type: "integer"
        required: true               # Required parameter
        min_value: 1
        description: "Unique identifier for the blog post"
```

**When to Use:** Getting detailed information about specific items.

#### Search Tool (Query Operations)

```yaml
  search_posts:
    type: "search"                   # Tool type for search/filter operations
    description: "Search posts by title keywords..."
    endpoint: "/posts"
    method: "GET"
    parameters:
      - name: "query"
        type: "string"
        required: true
        min_length: 2                # Minimum query length
        description: "Search query for post titles"
      - name: "sort"
        type: "string"
        required: false
        default: "date"
        enum: ["date", "title", "relevance"]  # Allowed values
        description: "Sort order for results"
```

**When to Use:** Complex queries, filtering, or search operations.

### Parameter Types and Validation

| Type | Validation Options | Example |
|------|-------------------|---------|
| `string` | `min_length`, `max_length`, `pattern`, `enum` | Text, IDs, status values |
| `integer` | `min_value`, `max_value` | Counts, IDs, limits |
| `number` | `min_value`, `max_value` | Prices, percentages |
| `boolean` | None | Flags, toggles |
| `array` | `items` | Lists of values |
| `object` | `properties` | Complex structures |

### Prompts (AI Assistance)

```yaml
prompts:
  content_assistant:
    name: "Content Analysis Assistant"
    description: "Expert assistant for analyzing blog content"
    content: |
      You are an expert content analyst...
      
      Available tools:
      - list_posts: Get overview of available blog posts
      - get_post: Retrieve detailed information about specific posts
      
      Guidelines:
      - Help users discover interesting content
      - Analyze post themes and patterns
```

**Purpose:** Provides context and instructions for AI assistants using the pack tools.

### Resources (Documentation)

```yaml
resources:
  api_docs:
    name: "JSONPlaceholder API Documentation"
    description: "Free REST API for testing and prototyping"
    type: "documentation"
    url: "https://jsonplaceholder.typicode.com/guide/"
```

**Purpose:** Links to helpful documentation, tutorials, and references.

## Usage Examples

### Using with MCP Server

If integrated with a Catalyst MCP server, tools become available as:

- `simple_rest_example_list_posts`
- `simple_rest_example_get_post`
- `simple_rest_example_search_posts`

### Example Queries

**List Recent Posts:**
```json
{
  "tool": "simple_rest_example_list_posts",
  "parameters": {
    "limit": 5
  }
}
```

**Get Specific Post:**
```json
{
  "tool": "simple_rest_example_get_post", 
  "parameters": {
    "post_id": 1
  }
}
```

**Search Posts:**
```json
{
  "tool": "simple_rest_example_search_posts",
  "parameters": {
    "query": "sunt aut",
    "sort": "relevance"
  }
}
```

## Extending This Example

### Add Authentication

For APIs requiring authentication:

```yaml
connection:
  auth:
    method: "basic"
    username: "${API_USER}"
    password: "${API_PASSWORD}"
```

### Add Request Body (POST/PUT)

```yaml
tools:
  create_post:
    type: "execute"
    description: "Create new blog post"
    endpoint: "/posts"
    method: "POST"
    parameters:
      - name: "title"
        type: "string"
        required: true
      - name: "body"
        type: "string"
        required: true
      - name: "userId"
        type: "integer"
        required: true
```

### Add Response Transformation

```yaml
tools:
  list_posts:
    # ... existing configuration ...
    transform:
      type: "jq"
      expression: '.[] | {id: .id, title: .title, summary: .body[:100] + "..."}'
```

### Add Custom Headers

```yaml
connection:
  headers:
    Accept: "application/json"
    Content-Type: "application/json"
    X-Custom-Header: "${CUSTOM_VALUE}"
```

## Best Practices Demonstrated

1. **Environment Variables:** All configuration values use environment variables
2. **Clear Descriptions:** Tool descriptions explain purpose and specify (READ-ONLY)
3. **Parameter Validation:** Appropriate constraints and validation rules
4. **Tool Types:** Correct tool types for different operations
5. **Documentation:** Comprehensive resource links
6. **Semantic Versioning:** Proper version numbering
7. **Domain Classification:** Clear business domain assignment

## Common Issues and Solutions

**Connection Timeout:**
- Increase `timeout` value in connection config
- Check network connectivity to API

**Authentication Errors:**
- Verify API_TOKEN is correct in .env file
- Check authentication method matches API requirements

**Parameter Validation Failures:**
- Ensure parameter types match API expectations
- Check min/max constraints are reasonable

**Endpoint Not Found:**
- Verify endpoint URLs in API documentation
- Check base_url is correct

This example provides a solid foundation for understanding Catalyst Knowledge Pack structure and can be adapted for any REST API integration.