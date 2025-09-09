"""Pack builder utilities for creating and scaffolding new packs."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from .models import Pack, PackMetadata, ConnectionConfig, ToolDefinition
from .validators import PackValidator


class PackBuilder:
    """Helper class for building and scaffolding catalyst packs."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._pack_dict = {
            "metadata": {
                "name": name,
                "version": version,
                "description": f"{name} integration pack",
                "author": "Pack Author",
                "license": "MIT",
                "compatibility": "2.0.0",
                "domain": "general",
                "vendor": "Community",
                "tags": [],
            },
            "connection": {"type": "rest"},
            "tools": {},
            "prompts": {},
            "resources": {},
        }

    @property
    def pack(self):
        """Get Pack object from current state."""
        from .models import Pack
        return Pack.from_dict(self._pack_dict)

    def set_metadata(self, **kwargs) -> "PackBuilder":
        """Set metadata fields."""
        self._pack_dict["metadata"].update(kwargs)
        return self

    def set_connection(self, type: str = None, connection_type: str = None, **kwargs) -> "PackBuilder":
        """Configure connection settings."""
        # Support both 'type' and 'connection_type' parameters for backwards compatibility
        conn_type = type or connection_type
        if not conn_type:
            raise ValueError("Either 'type' or 'connection_type' must be specified")
        
        self._pack_dict["connection"] = {"type": conn_type, **kwargs}
        return self
    
    def set_auth(self, method: str, **kwargs) -> "PackBuilder":
        """Set authentication configuration."""
        if "connection" not in self._pack_dict:
            self._pack_dict["connection"] = {}
        
        self._pack_dict["connection"]["auth"] = {
            "method": method,
            "config": kwargs
        }
        return self

    def add_rest_connection(
        self, base_url: str, auth_method: Optional[str] = None
    ) -> "PackBuilder":
        """Add REST API connection configuration."""
        connection = {"type": "rest", "base_url": base_url}
        if auth_method:
            connection["auth"] = {"method": auth_method}
        self._pack_dict["connection"] = connection
        return self

    def add_tool(self, name: str, tool_type: str, description: str, **kwargs) -> "PackBuilder":
        """Add a tool to the pack."""
        tool = {"type": tool_type, "description": description, **kwargs}
        self._pack_dict["tools"][name] = tool
        return self

    def add_prompt(self, prompt_key: str, **kwargs) -> "PackBuilder":
        """Add a prompt template."""
        # Extract required fields, set defaults
        prompt = {
            "name": kwargs.get("name", prompt_key),
            "description": kwargs.get("description", f"Prompt for {prompt_key}"),
            "template": kwargs.get("template", ""),
            **{k: v for k, v in kwargs.items() if k not in ["name", "description", "template"]}
        }
        self._pack_dict["prompts"][prompt_key] = prompt
        return self

    def add_resource(self, resource_key: str, **kwargs) -> "PackBuilder":
        """Add a resource definition."""
        # Extract required fields
        resource = {
            "name": kwargs.get("name", resource_key),
            "type": kwargs.get("type", "documentation"),
            **{k: v for k, v in kwargs.items() if k not in ["name", "type"]}
        }
        self._pack_dict["resources"][resource_key] = resource
        return self

    def validate(self) -> bool:
        """Validate the current pack configuration."""
        validator = PackValidator()
        result = validator.validate_pack_dict(self.pack)
        if not result.is_valid:
            print(f"Validation errors: {result.errors}")
        return result.is_valid

    def build(self):
        """Build and return the pack object."""
        return self.pack

    def save(self, output_dir: str) -> Path:
        """Save the pack to a YAML file and return the pack directory."""
        pack_dir = Path(output_dir) / self.name
        pack_dir.mkdir(parents=True, exist_ok=True)
        
        pack_file = pack_dir / "pack.yaml"
        with open(pack_file, "w") as f:
            yaml.dump(self._pack_dict, f, default_flow_style=False, sort_keys=False)
        print(f"Pack saved to {pack_file}")
        return pack_dir

    def scaffold(self, output_dir: str) -> Path:
        """Create a complete pack directory structure."""
        pack_dir = Path(output_dir) / self.name
        pack_dir.mkdir(parents=True, exist_ok=True)

        # Create pack.yaml
        pack_file = pack_dir / "pack.yaml"
        with open(pack_file, "w") as f:
            yaml.dump(self._pack_dict, f, default_flow_style=False, sort_keys=False)

        # Create modular structure based on connection type
        self._create_modular_structure(pack_dir)

        # Create README
        self._create_readme(pack_dir)

        # Create .env file
        self._create_env_file(pack_dir)

        print(f"Pack scaffolded in {pack_dir}")
        return pack_dir

    def _create_modular_structure(self, pack_dir: Path) -> None:
        """Create modular directory structure with example files."""
        connection_type = self._pack_dict.get("connection", {}).get("type", "rest")

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

{self._pack_dict['metadata'].get('description', f'{self.name} integration pack')}

## Overview

This pack provides integration capabilities for {self.name} systems through the Catalyst Knowledge Pack framework.

### Pack Information

- **Name:** {self.name}
- **Version:** {self._pack_dict['metadata'].get('version', '1.0.0')}
- **Domain:** {self._pack_dict['metadata'].get('domain', 'general')}
- **Vendor:** {self._pack_dict['metadata'].get('vendor', 'Community')}
- **Connection Type:** {self._pack_dict.get('connection', {}).get('type', 'unknown')}"

## Configuration

### Environment Variables

Set the following environment variables for this pack:

"""

        connection = self._pack_dict.get("connection", {})
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

    def _create_env_file(self, pack_dir: Path) -> None:
        """Create .env file with environment variable templates."""
        connection = self._pack_dict.get("connection", {})
        connection_type = connection.get("type", "rest")
        
        env_content = f"# Environment variables for {self.name}\n"
        env_content += "# Copy this file to .env and fill in your actual values\n\n"
        
        if connection_type == "rest":
            env_content += "# REST API Configuration\n"
            env_content += "API_BASE_URL=https://your-api-domain.com\n"
            env_content += "API_TOKEN=your_api_token_here\n"
        elif connection_type == "database":
            env_content += "# Database Configuration\n"
            env_content += "DB_HOST=localhost\n"
            env_content += "DB_PORT=5432\n"
            env_content += "DB_NAME=your_database\n"
            env_content += "DB_USER=your_username\n"
            env_content += "DB_PASSWORD=your_password\n"
        elif connection_type == "ssh":
            env_content += "# SSH Configuration\n"
            env_content += "SSH_HOST=your-server.com\n"
            env_content += "SSH_USER=your_username\n"
            env_content += "SSH_KEY_PATH=~/.ssh/id_rsa\n"
        
        env_content += f"\n# Pack: {self.name}\n"
        env_content += f"# Generated by catalyst-builder\n"
        
        with open(pack_dir / ".env", "w", encoding="utf-8") as f:
            f.write(env_content)

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
        valid_connection_types = ["rest", "database", "ssh", "filesystem", "message_queue"]
        
        if connection_type == "rest":
            conn_config = {
                "connection_type": "rest",
                "base_url": base_url or "${API_BASE_URL}",
                "timeout": 30,
            }
            # Add auth if provided
            if "auth_method" in kwargs:
                auth_config = {"method": kwargs["auth_method"]}
                if "auth_token" in kwargs:
                    auth_config["token"] = kwargs["auth_token"]
                else:
                    auth_config["token"] = "${API_TOKEN}"
                conn_config["auth"] = auth_config
            else:
                conn_config["auth"] = {"method": "bearer", "token": "${API_TOKEN}"}
            
            builder.set_connection(**conn_config)
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
                hostname=kwargs.get("hostname", "${SSH_HOST}"),
                username=kwargs.get("username", "${SSH_USER}"),
                auth={"method": "ssh_key", "key_path": "${SSH_KEY_PATH}"},
            )
        elif connection_type in valid_connection_types:
            builder.set_connection(connection_type=connection_type, **kwargs)
        else:
            raise ValueError(f"Unsupported connection type: {connection_type}. Valid types: {valid_connection_types}")

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
    def create_database_pack(name: str, engine: str = "postgresql", **kwargs):
        """Create a database integration pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=f"Database integration for {name}",
            vendor=kwargs.get("vendor", "Community"),
            domain=kwargs.get("domain", "data"),
            tags=["database", engine, "sql"]
        )
        builder.set_connection(
            type="database",
            engine=engine,
            host=kwargs.get("host", "${DB_HOST}"),
            port=kwargs.get("port", "${DB_PORT}"),
            database=kwargs.get("database", "${DB_NAME}"),
        )

        return builder.pack

    @staticmethod
    def create_rest_pack(name: str, base_url: str, description: str = "", **kwargs):
        """Create a REST API integration pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=description or f"REST API integration for {name}",
            vendor=kwargs.get("vendor", "Community"),
            domain=kwargs.get("domain", "api"),
            tags=["rest", "api", "integration"],
        )
        builder.set_connection(type="rest", base_url=base_url)
        
        # Add auth if provided
        if "auth_method" in kwargs:
            auth_config = {"method": kwargs["auth_method"]}
            if "auth_token" in kwargs:
                auth_config["token"] = kwargs["auth_token"]
            builder.set_auth(**auth_config)
        
        return builder.pack

    @staticmethod
    def create_ssh_pack(name: str, hostname: str, username: str, description: str = "", **kwargs):
        """Create an SSH integration pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=description or f"SSH integration for {name}",
            vendor=kwargs.get("vendor", "Community"),
            domain=kwargs.get("domain", "infrastructure"),
            tags=["ssh", "infrastructure", "remote"],
        )
        builder.set_connection(type="ssh", hostname=hostname, username=username)
        return builder.pack

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


def quick_pack(name: str, connection_type: str = "rest", output_dir: str = None, **kwargs) -> Path:
    """Quick helper to create common pack types and save them."""
    if not output_dir:
        raise ValueError("output_dir is required for quick_pack")
        
    builder = PackBuilder(name)
    
    if connection_type == "rest":
        builder.set_metadata(
            description=kwargs.get("description", f"REST API integration for {name}"),
            vendor=kwargs.get("vendor", "Community"),
            domain=kwargs.get("domain", "api"),
            tags=["rest", "api", "integration"],
        )
        builder.set_connection(type="rest", base_url=kwargs.get("base_url", "${API_BASE_URL}"))
    elif connection_type == "database":
        builder.set_metadata(
            description=kwargs.get("description", f"Database integration for {name}"),
            vendor=kwargs.get("vendor", "Community"),
            domain=kwargs.get("domain", "data"),
            tags=["database", kwargs.get("engine", "postgresql"), "sql"]
        )
        builder.set_connection(
            type="database",
            engine=kwargs.get("engine", "postgresql"),
            host=kwargs.get("host", "${DB_HOST}"),
            port=kwargs.get("port", "${DB_PORT}"),
            database=kwargs.get("database", "${DB_NAME}"),
        )
    else:
        builder.set_metadata(
            description=kwargs.get("description", f"{name} integration pack"),
            vendor=kwargs.get("vendor", "Community"),
            domain=kwargs.get("domain", "general"),
        )
        builder.set_connection(type=connection_type, **kwargs)
    
    return builder.save(output_dir)


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
