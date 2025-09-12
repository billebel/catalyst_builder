# LLM Optimization Features (v1.1.0+)

This guide covers the new optional features added in v1.1.0 to help optimize Knowledge Packs for LLM usage.

## Overview

Catalyst Builder v1.1.0 introduces optional fields designed to improve how Large Language Models (LLMs) discover, understand, and use your tools. These features are completely optional and maintain 100% backward compatibility.

## LLM Metadata for Tools

### Basic Usage

Add an `llm_metadata` section to any tool to provide LLM-friendly guidance:

```yaml
tools:
  search_users:
    type: "search"
    description: "Search for users in the system"
    endpoint: "/users/search"
    
    # LLM optimization (optional)
    llm_metadata:
      display_name: "🔍 Search Users"
      usage_hint: "Use this when the user asks about finding or looking up users"
      complexity: "basic"
      
      examples:
        - scenario: "User asks 'find users named John'"
          usage: "Use search_term parameter with 'John'"
        - scenario: "User wants to see all admin users"
          usage: "Use role parameter with 'admin'"
```

### LLM Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `display_name` | string | Human-friendly name, often with emojis for visual hierarchy |
| `usage_hint` | string | Guidance on when an LLM should use this tool |
| `complexity` | enum | `basic`, `intermediate`, or `advanced` |
| `prerequisites` | array | List of tools that should be used before this one |
| `examples` | array | Usage scenarios with explanations |

### Example with Prerequisites

```yaml
tools:
  execute_search:
    type: "execute"
    description: "Execute a complex search query"
    
    llm_metadata:
      display_name: "⚡ Execute Search"
      complexity: "advanced"
      prerequisites: ["search_indexes", "validate_query"]
      usage_hint: "Use only after exploring available data sources"
```

## Parameter Constraints

### Basic Constraints

Add validation and guidance to parameters:

```yaml
parameters:
  - name: "limit"
    type: "integer"
    description: "Maximum results to return"
    constraints:
      min: 1
      max: 1000
      examples: [10, 25, 50, 100]
      
  - name: "query"
    type: "string"
    description: "Search query"
    constraints:
      min_length: 1
      max_length: 500
      pattern: "^[a-zA-Z0-9\\s\\-_]+$"
      examples: ["user:john", "status:active", "created:2024"]
```

### Constraint Types

| Field | Applies To | Description |
|-------|------------|-------------|
| `min` / `max` | integer, number | Numeric value bounds |
| `min_length` / `max_length` | string | String length limits |
| `pattern` | string | Regular expression validation |
| `examples` | all types | Example values to guide LLM choices |

## Advanced Transform Features (Pre-existing)

### External Transform Files

Instead of inline code, reference external files for better maintainability:

```yaml
tools:
  process_data:
    type: "search"
    description: "Process and clean search results"
    endpoint: "/data"
    
    transform:
      type: "python"
      file: "transforms/data_processor.py"  # External file
      function: "clean_results"              # Function to call
```

### Form Data and Query Parameters

Handle complex API interactions:

```yaml
tools:
  advanced_search:
    type: "search"
    description: "Advanced search with multiple parameters"
    endpoint: "/search"
    method: "POST"
    
    # URL query parameters
    query_params:
      format: "json"
      version: "v2"
    
    # Form-encoded body
    form_data:
      q: "{search_query}"
      limit: "{max_results}"
      filters: "{filter_json}"
```

## Best Practices

### 1. Progressive Disclosure

Use complexity levels to guide LLMs from simple to advanced tools:

```yaml
# Basic discovery tool
discover_data:
  llm_metadata:
    complexity: "basic"
    usage_hint: "Start here to explore available data"

# Intermediate analysis  
analyze_data:
  llm_metadata:
    complexity: "intermediate" 
    prerequisites: ["discover_data"]

# Advanced operations
execute_query:
  llm_metadata:
    complexity: "advanced"
    prerequisites: ["discover_data", "analyze_data"]
```

### 2. Clear Visual Hierarchy

Use emojis strategically in display names:

```yaml
# Discovery tools
display_name: "📊 List Available Data"
display_name: "🔍 Search Records" 
display_name: "🏷️ Show Categories"

# Action tools
display_name: "⚡ Execute Query"
display_name: "💾 Save Results"
display_name: "📤 Export Data"

# Warning tools  
display_name: "⚠️ Delete Records"
display_name: "🚨 Reset System"
```

### 3. Helpful Examples

Provide concrete, realistic examples:

```yaml
constraints:
  examples:
    # Good: Specific and realistic
    - "user:john.doe@company.com"
    - "status:active AND department:engineering" 
    - "created:>2024-01-01"
    
    # Avoid: Too generic
    - "search term"
    - "example query"
```

### 4. Prerequisites for Safety

Use prerequisites to enforce safe workflows:

```yaml
tools:
  delete_user:
    llm_metadata:
      display_name: "🗑️ Delete User"
      complexity: "advanced"
      prerequisites: ["search_users", "confirm_user"]  # Safety first!
      usage_hint: "Only use after confirming the correct user"
```

## Migration Guide

### From v1.0.x to v1.1.0

1. **No changes required** - All existing packs continue to work
2. **Gradual adoption** - Add LLM metadata to tools over time  
3. **Test compatibility** - Run existing validation to ensure no breaks

### Adding LLM Features to Existing Packs

```yaml
# Before (v1.0.x - still works)
tools:
  get_users:
    type: "list"
    description: "Get users"
    endpoint: "/users"

# After (v1.1.0 - enhanced)  
tools:
  get_users:
    type: "list" 
    description: "Get users"
    endpoint: "/users"
    
    # Add LLM optimization
    llm_metadata:
      display_name: "👥 Get Users"
      usage_hint: "Use this to see all users in the system"
      complexity: "basic"
```

## Validation

The schema validator automatically handles both old and new formats:

```python
from catalyst_pack_schemas.validators import PackValidator

validator = PackValidator()

# Works with v1.0.x packs (no LLM fields)
old_pack = Pack.from_dict(old_pack_data)
assert validator.validate_pack(old_pack) == True

# Works with v1.1.0 packs (with LLM fields)  
new_pack = Pack.from_dict(new_pack_data)
assert validator.validate_pack(new_pack) == True
```

All new features are optional and won't cause validation errors if omitted.