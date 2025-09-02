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
        self.pack = {
            "metadata": {
                "name": name,
                "version": version,
                "description": f"{name} integration pack",
                "author": "Pack Author",
                "tags": []
            },
            "connection": {},
            "tools": [],
            "prompts": [],
            "resources": []
        }
    
    def set_metadata(self, **kwargs) -> "PackBuilder":
        """Set metadata fields."""
        self.pack["metadata"].update(kwargs)
        return self
    
    def set_connection(self, connection_type: str, **kwargs) -> "PackBuilder":
        """Configure connection settings."""
        self.pack["connection"] = {
            "type": connection_type,
            **kwargs
        }
        return self
    
    def add_rest_connection(self, base_url: str, auth_method: Optional[str] = None) -> "PackBuilder":
        """Add REST API connection configuration."""
        connection = {
            "type": "rest",
            "base_url": base_url
        }
        if auth_method:
            connection["auth"] = {"method": auth_method}
        self.pack["connection"] = connection
        return self
    
    def add_tool(self, name: str, tool_type: str, description: str, **kwargs) -> "PackBuilder":
        """Add a tool to the pack."""
        tool = {
            "name": name,
            "type": tool_type,
            "description": description,
            **kwargs
        }
        self.pack["tools"].append(tool)
        return self
    
    def add_prompt(self, name: str, template: str, description: str = "") -> "PackBuilder":
        """Add a prompt template."""
        prompt = {
            "name": name,
            "description": description or f"Prompt for {name}",
            "template": template
        }
        self.pack["prompts"].append(prompt)
        return self
    
    def add_resource(self, name: str, resource_type: str, **kwargs) -> "PackBuilder":
        """Add a resource definition."""
        resource = {
            "name": name,
            "type": resource_type,
            **kwargs
        }
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
        with open(filepath, 'w') as f:
            yaml.dump(self.pack, f, default_flow_style=False, sort_keys=False)
        print(f"Pack saved to {filepath}")
    
    def scaffold(self, output_dir: str) -> None:
        """Create a complete pack directory structure."""
        pack_dir = Path(output_dir) / self.name
        pack_dir.mkdir(parents=True, exist_ok=True)
        
        # Create pack.yaml
        pack_file = pack_dir / "pack.yaml"
        self.save(str(pack_file))
        
        # Create tools directory if tools exist
        if self.pack.get("tools"):
            tools_dir = pack_dir / "tools"
            tools_dir.mkdir(exist_ok=True)
            
            for tool in self.pack["tools"]:
                tool_file = tools_dir / f"{tool['name']}.yaml"
                with open(tool_file, 'w') as f:
                    yaml.dump(tool, f, default_flow_style=False)
        
        # Create prompts directory if prompts exist
        if self.pack.get("prompts"):
            prompts_dir = pack_dir / "prompts"
            prompts_dir.mkdir(exist_ok=True)
            
            for prompt in self.pack["prompts"]:
                prompt_file = prompts_dir / f"{prompt['name']}.yaml"
                with open(prompt_file, 'w') as f:
                    yaml.dump(prompt, f, default_flow_style=False)
        
        # Create README
        readme_file = pack_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(f"# {self.name}\n\n")
            f.write(f"{self.pack['metadata'].get('description', '')}\n\n")
            f.write("## Tools\n\n")
            for tool in self.pack.get("tools", []):
                f.write(f"- **{tool['name']}**: {tool['description']}\n")
        
        print(f"Pack scaffolded in {pack_dir}")


class PackFactory:
    """Factory for creating common pack types."""
    
    @staticmethod
    def create_rest_api_pack(name: str, base_url: str, description: str = "") -> PackBuilder:
        """Create a REST API integration pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=description or f"REST API integration for {name}",
            tags=["rest", "api", "integration"]
        )
        builder.add_rest_connection(base_url, auth_method="bearer")
        
        # Add common REST tools
        builder.add_tool(
            name="list_items",
            tool_type="list",
            description="List all items",
            endpoint="/items"
        )
        builder.add_tool(
            name="get_item",
            tool_type="details",
            description="Get item details",
            endpoint="/items/{id}"
        )
        builder.add_tool(
            name="search",
            tool_type="search",
            description="Search items",
            endpoint="/search"
        )
        
        return builder
    
    @staticmethod
    def create_database_pack(name: str, engine: str = "postgresql") -> PackBuilder:
        """Create a database integration pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=f"Database integration for {name}",
            tags=["database", engine, "sql"]
        )
        builder.set_connection(
            connection_type="database",
            engine=engine,
            host="${DB_HOST}",
            port="${DB_PORT}",
            database="${DB_NAME}"
        )
        
        # Add common database tools
        builder.add_tool(
            name="execute_query",
            tool_type="query",
            description="Execute SQL query",
            query_template="SELECT * FROM {table} LIMIT 100"
        )
        builder.add_tool(
            name="list_tables",
            tool_type="list", 
            description="List database tables",
            query_template="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        
        return builder
    
    @staticmethod
    def create_monitoring_pack(name: str, system: str) -> PackBuilder:
        """Create a monitoring/observability pack."""
        builder = PackBuilder(name)
        builder.set_metadata(
            description=f"Monitoring integration for {system}",
            tags=["monitoring", "observability", "metrics"]
        )
        
        # Add common monitoring tools
        builder.add_tool(
            name="get_metrics",
            tool_type="query",
            description="Retrieve system metrics",
            endpoint="/metrics"
        )
        builder.add_tool(
            name="get_alerts",
            tool_type="list",
            description="List active alerts",
            endpoint="/alerts"
        )
        builder.add_tool(
            name="get_health",
            tool_type="details",
            description="Get system health status",
            endpoint="/health"
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