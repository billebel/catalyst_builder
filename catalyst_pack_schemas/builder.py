"""Pack builder utilities for creating and scaffolding new packs."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import ConnectionConfig, Pack, PackMetadata, ToolDefinition
from .validators import PackValidator


class PackBuilder:
    """Helper class for building and scaffolding catalyst packs."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.pack = {
            "metadata": {
                "name": name,
                "version": version,
                "description": f"{name} integration pack",
                "author": "Pack Author",
                "tags": [],
            },
            "connection": {},
            "tools": [],
            "prompts": [],
            "resources": [],
        }

    def set_metadata(self, **kwargs) -> "PackBuilder":
        """Set metadata fields."""
        self.pack["metadata"].update(kwargs)
        return self

    def set_connection(self, connection_type: str, **kwargs) -> "PackBuilder":
        """Configure connection settings."""
        self.pack["connection"] = {"type": connection_type, **kwargs}
        return self

    def add_rest_connection(
        self, base_url: str, auth_method: Optional[str] = None
    ) -> "PackBuilder":
        """Add REST API connection configuration."""
        connection = {"type": "rest", "base_url": base_url}
        if auth_method:
            connection["auth"] = {"method": auth_method}
        self.pack["connection"] = connection
        return self

    def add_tool(self, name: str, tool_type: str, description: str, **kwargs) -> "PackBuilder":
        """Add a tool to the pack."""
        tool = {"name": name, "type": tool_type, "description": description, **kwargs}
        self.pack["tools"].append(tool)
        return self

    def add_prompt(self, name: str, template: str, description: str = "") -> "PackBuilder":
        """Add a prompt template."""
        prompt = {
            "name": name,
            "description": description or f"Prompt for {name}",
            "template": template,
        }
        self.pack["prompts"].append(prompt)
        return self

    def add_resource(self, name: str, resource_type: str, **kwargs) -> "PackBuilder":
        """Add a resource definition."""
        resource = {"name": name, "type": resource_type, **kwargs}
        self.pack["resources"].append(resource)
        return self

    def validate(self) -> bool:
        """Validate the current pack configuration."""
        validator = PackValidator()
        result = validator.validate_pack_dict(self.pack)
        if not result.is_valid:
            print(f"Validation errors: {result.errors}")
        return result.is_valid

    def build(self) -> Dict[str, Any]:
        """Build and return the pack dictionary."""
        return self.pack

    def save(self, filepath: str) -> None:
        """Save the pack to a YAML file."""
        with open(filepath, "w") as f:
            yaml.dump(self.pack, f, default_flow_style=False, sort_keys=False)
        print(f"Pack saved to {filepath}")

    def scaffold(self, output_dir: str) -> Path:
        """Create a complete pack directory structure."""
        pack_dir = Path(output_dir) / self.name
        pack_dir.mkdir(parents=True, exist_ok=True)

        # Create pack.yaml
        pack_file = pack_dir / "pack.yaml"
        self.save(str(pack_file))

        # Create modular structure based on connection type
        self._create_modular_structure(pack_dir)

        # Create README
        self._create_readme(pack_dir)

        print(f"Pack scaffolded in {pack_dir}")
        return pack_dir

    def _create_modular_structure(self, pack_dir: Path) -> None:
        """Create modular directory structure with example files."""
        connection_type = self.pack.get("connection", {}).get("type", "rest")

        # Create tools directory with examples
        tools_dir = pack_dir / "tools"
        tools_dir.mkdir(exist_ok=True)

        tools_data = {"tools": {}}

        if connection_type == "rest":
            tools_data["tools"].update(
                {
                    "list_items": {
                        "type": "list",
                        "description": "List all items from the API",
                        "endpoint": "/api/items",
                        "method": "GET",
                        "parameters": [
                            {
                                "name": "limit",
                                "type": "integer",
                                "default": 20,
                                "description": "Maximum items to return",
                            }
                        ],
                    },
                    "search_items": {
                        "type": "search",
                        "description": "Search items by query",
                        "endpoint": "/api/search",
                        "method": "POST",
                        "parameters": [
                            {
                                "name": "query",
                                "type": "string",
                                "required": True,
                                "description": "Search query",
                            }
                        ],
                    },
                }
            )
        elif connection_type == "database":
            tools_data["tools"].update(
                {
                    "query_data": {
                        "type": "query",
                        "description": "Execute SQL query on database",
                        "sql": "SELECT * FROM {table} WHERE {condition} LIMIT {limit}",
                        "parameters": [
                            {
                                "name": "table",
                                "type": "string",
                                "required": True,
                                "description": "Table name to query",
                            }
                        ],
                    },
                    "list_tables": {
                        "type": "list",
                        "description": "List all database tables",
                        "sql": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
                    },
                }
            )
        elif connection_type == "ssh":
            tools_data["tools"].update(
                {
                    "execute_command": {
                        "type": "execute",
                        "description": "Execute command on remote server",
                        "command": "{command}",
                        "parameters": [
                            {
                                "name": "command",
                                "type": "string",
                                "required": True,
                                "description": "Command to execute",
                            }
                        ],
                    }
                }
            )

        with open(tools_dir / "example-tools.yaml", "w") as f:
            yaml.dump(tools_data, f, default_flow_style=False, sort_keys=False)

        # Create prompts directory with examples
        prompts_dir = pack_dir / "prompts"
        prompts_dir.mkdir(exist_ok=True)

        prompts_data = {
            "prompts": {
                "data_analyst": {
                    "name": "Data Analysis Assistant",
                    "description": f"Assistant for analyzing {self.name} data",
                    "content": f"You are an expert data analyst specializing in {self.name} systems. Help analyze the provided data and extract meaningful insights.",
                }
            }
        }

        with open(prompts_dir / "analysis-prompts.yaml", "w") as f:
            yaml.dump(prompts_data, f, default_flow_style=False, sort_keys=False)

        # Create resources directory with examples
        resources_dir = pack_dir / "resources"
        resources_dir.mkdir(exist_ok=True)

        resources_data = {
            "resources": {
                "api_documentation": {
                    "name": f"{self.name} API Documentation",
                    "type": "documentation",
                    "description": f"Official API documentation for {self.name}",
                    "url": "${API_DOC_URL}",
                }
            }
        }

        with open(resources_dir / "documentation.yaml", "w") as f:
            yaml.dump(resources_data, f, default_flow_style=False, sort_keys=False)

        # Create transforms directory (optional)
        transforms_dir = pack_dir / "transforms"
        transforms_dir.mkdir(exist_ok=True)

        transform_script = f'''"""
Transform scripts for {self.name} pack.

These scripts can be used to transform data between different formats
or to perform custom processing on API responses.
"""

def transform_response(data):
    """Transform API response data."""
    # Add your transformation logic here
    return data

def format_output(data):
    """Format data for output."""
    # Add your formatting logic here  
    return data
'''

        with open(transforms_dir / "transform.py", "w") as f:
            f.write(transform_script)

    def _create_readme(self, pack_dir: Path) -> None:
        """Create comprehensive README file."""
        readme_content = f"""# {self.name}

{self.pack['metadata'].get('description', f'{self.name} integration pack')}

## Overview

This pack provides integration capabilities for {self.name} systems through the Catalyst Knowledge Pack framework.

### Pack Information

- **Name:** {self.name}
- **Version:** {self.pack['metadata'].get('version', '1.0.0')}
- **Domain:** {self.pack['metadata'].get('domain', 'general')}
- **Vendor:** {self.pack['metadata'].get('vendor', 'Community')}
- **Connection Type:** {self.pack.get('connection', {}).get('type', 'unknown')}

## Configuration

### Environment Variables

Set the following environment variables for this pack:

"""

        connection = self.pack.get("connection", {})
        if connection.get("type") == "rest":
            readme_content += """- `API_BASE_URL` - Base URL for the API
- `API_TOKEN` - Authentication token
"""
        elif connection.get("type") == "database":
            readme_content += """- `DB_HOST` - Database host
- `DB_PORT` - Database port  
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
"""
        elif connection.get("type") == "ssh":
            readme_content += """- `SSH_HOST` - SSH hostname
- `SSH_USER` - SSH username
- `SSH_KEY_PATH` - Path to SSH private key
"""

        readme_content += f"""
## Tools

This pack provides the following tools:

"""

        # Add tool descriptions from example files
        connection_type = connection.get("type", "rest")
        if connection_type == "rest":
            readme_content += """- **list_items** - List all items from the API
- **search_items** - Search items by query
"""
        elif connection_type == "database":
            readme_content += """- **query_data** - Execute SQL queries on the database  
- **list_tables** - List all database tables
"""
        elif connection_type == "ssh":
            readme_content += """- **execute_command** - Execute commands on the remote server
"""

        readme_content += f"""
## Directory Structure

```
{self.name}/
├── pack.yaml           # Pack configuration
├── tools/             # Tool definitions
├── prompts/           # Prompt templates
├── resources/         # Resource definitions
├── transforms/        # Transform scripts
└── README.md         # This file
```

## Development

### Testing the Pack

1. Validate the pack structure:
   ```bash
   catalyst-packs validate {self.name}/
   ```

2. Test individual tools using the Catalyst framework

### Contributing

When modifying this pack:

1. Update the version in `pack.yaml`
2. Test all tools thoroughly
3. Update this README with any new tools or configuration changes
4. Validate the pack before deploying

## Support

For issues related to this pack, please check:

1. Environment variable configuration
2. Network connectivity to target systems
3. Authentication credentials
4. Pack validation results

---

Generated by catalyst-builder v1.0.0
"""

        with open(pack_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def create_pack(
        self,
        pack_name: str,
        output_dir: str,
        connection_type: str = "rest",
        domain: str = "general",
        vendor: str = "Community",
        base_url: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> Path:
        """Create a complete pack with directory structure (static method alternative)."""
        # Create new builder instance
        builder = PackBuilder(pack_name)

        # Set metadata
        builder.set_metadata(
            description=description or f"{pack_name} integration pack",
            domain=domain,
            vendor=vendor,
            tags=[connection_type, domain.replace("_", "-")],
        )

        # Configure connection
        if connection_type == "rest":
            builder.set_connection(
                connection_type="rest",
                base_url=base_url or "${API_BASE_URL}",
                auth={"method": "bearer", "token": "${API_TOKEN}"},
                timeout=30,
            )
        elif connection_type == "database":
            builder.set_connection(
                connection_type="database",
                engine=kwargs.get("engine", "postgresql"),
                host="${DB_HOST}",
                port="${DB_PORT}",
                database="${DB_NAME}",
                auth={"method": "basic", "username": "${DB_USER}", "password": "${DB_PASSWORD}"},
            )
        elif connection_type == "ssh":
            builder.set_connection(
                connection_type="ssh",
                hostname="${SSH_HOST}",
                username="${SSH_USER}",
                auth={"method": "ssh_key", "key_path": "${SSH_KEY_PATH}"},
            )
        else:
            builder.set_connection(connection_type=connection_type, **kwargs)

        # Create the pack directory structure
        return builder.scaffold(output_dir)


class PackFactory:
    """Factory for creating common pack types."""

    @staticmethod
    def create_rest_api_pack(name: str, base_url: str, description: str = "") -> PackBuilder:
        """Create a REST API integration pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=description or f"REST API integration for {name}",
            tags=["rest", "api", "integration"],
        )
        builder.add_rest_connection(base_url, auth_method="bearer")

        # Add common REST tools
        builder.add_tool(
            name="list_items", tool_type="list", description="List all items", endpoint="/items"
        )
        builder.add_tool(
            name="get_item",
            tool_type="details",
            description="Get item details",
            endpoint="/items/{id}",
        )
        builder.add_tool(
            name="search", tool_type="search", description="Search items", endpoint="/search"
        )

        return builder

    @staticmethod
    def create_database_pack(name: str, engine: str = "postgresql") -> PackBuilder:
        """Create a database integration pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=f"Database integration for {name}", tags=["database", engine, "sql"]
        )
        builder.set_connection(
            connection_type="database",
            engine=engine,
            host="${DB_HOST}",
            port="${DB_PORT}",
            database="${DB_NAME}",
        )

        # Add common database tools
        builder.add_tool(
            name="execute_query",
            tool_type="query",
            description="Execute SQL query",
            query_template="SELECT * FROM {table} LIMIT 100",
        )
        builder.add_tool(
            name="list_tables",
            tool_type="list",
            description="List database tables",
            query_template="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
        )

        return builder

    @staticmethod
    def create_monitoring_pack(name: str, system: str) -> PackBuilder:
        """Create a monitoring/observability pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=f"Monitoring integration for {system}",
            tags=["monitoring", "observability", "metrics"],
        )

        # Add common monitoring tools
        builder.add_tool(
            name="get_metrics",
            tool_type="query",
            description="Retrieve system metrics",
            endpoint="/metrics",
        )
        builder.add_tool(
            name="get_alerts",
            tool_type="list",
            description="List active alerts",
            endpoint="/alerts",
        )
        builder.add_tool(
            name="get_health",
            tool_type="details",
            description="Get system health status",
            endpoint="/health",
        )

        return builder


def quick_pack(name: str, pack_type: str = "rest", **kwargs) -> PackBuilder:
    """Quick helper to create common pack types."""
    if pack_type == "rest":
        return PackFactory.create_rest_api_pack(name, **kwargs)
    elif pack_type == "database":
        return PackFactory.create_database_pack(name, **kwargs)
    elif pack_type == "monitoring":
        return PackFactory.create_monitoring_pack(name, **kwargs)
    else:
        return PackBuilder(name)


def create_pack(
    pack_name: str,
    output_dir: str,
    connection_type: str = "rest",
    domain: str = "general",
    vendor: str = "Community",
    base_url: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs,
) -> Path:
    """Create a complete pack with directory structure (standalone function)."""
    builder = PackBuilder(pack_name)
    return builder.create_pack(
        pack_name=pack_name,
        output_dir=output_dir,
        connection_type=connection_type,
        domain=domain,
        vendor=vendor,
        base_url=base_url,
        description=description,
        **kwargs,
    )
