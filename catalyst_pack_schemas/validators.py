"""Validation utilities for knowledge packs."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import Pack, PackValidationError


class PackValidator:
    """Validates knowledge pack configurations."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_pack(self, pack: Pack) -> bool:
        """Validate a Pack object.

        Args:
            pack: Pack object to validate

        Returns:
            True if valid, False otherwise
        """
        self.errors.clear()
        self.warnings.clear()

        self._validate_metadata(pack.metadata)
        self._validate_connection(pack.connection)
        self._validate_tools(pack.tools, pack.structure)
        self._validate_prompts(pack.prompts)
        self._validate_resources(pack.resources)

        return len(self.errors) == 0

    def _validate_metadata(self, metadata) -> None:
        """Validate pack metadata."""
        if not metadata.name:
            self.errors.append("metadata.name is required")

        if not metadata.version:
            self.errors.append("metadata.version is required")

        if not metadata.description:
            self.errors.append("metadata.description is required")

        if not metadata.vendor:
            self.errors.append("metadata.vendor is required")

        if not metadata.domain:
            self.errors.append("metadata.domain is required")

        # Validate version format (semantic versioning)
        if metadata.version:
            version_parts = metadata.version.split(".")
            if len(version_parts) != 3:
                self.warnings.append("Version should follow semantic versioning (x.y.z)")

        # Validate pricing tier
        valid_tiers = ["free", "basic", "premium", "enterprise"]
        if metadata.pricing_tier not in valid_tiers:
            self.errors.append(
                f"Invalid pricing_tier: {metadata.pricing_tier}. Must be one of: {valid_tiers}"
            )

    def _validate_connection(self, connection) -> None:
        """Validate connection configuration."""
        if not connection.type:
            self.errors.append("connection.type is required")
            return

        valid_types = [
            "rest",
            "database",
            "message_queue",
            "filesystem",
            "ssh",
            "grpc",
            "websocket",
        ]
        if connection.type not in valid_types:
            self.errors.append(
                f"Invalid connection.type: {connection.type}. Must be one of: {valid_types}"
            )

        # Type-specific validation
        if connection.type == "rest":
            if not connection.base_url:
                self.errors.append("connection.base_url is required for REST connections")

        elif connection.type == "database":
            if not connection.engine:
                self.errors.append("connection.engine is required for database connections")
            if not connection.host:
                self.errors.append("connection.host is required for database connections")

        elif connection.type == "ssh":
            if not connection.hostname:
                self.errors.append("connection.hostname is required for SSH connections")
            if not connection.username:
                self.errors.append("connection.username is required for SSH connections")

        # Validate timeout
        if connection.timeout <= 0:
            self.errors.append("connection.timeout must be positive")

        # Validate auth if present
        if connection.auth:
            if not connection.auth.method:
                self.errors.append("connection.auth.method is required when auth is specified")

    def _validate_tools(self, tools: Dict[str, Any], structure: Optional[Dict] = None) -> None:
        """Validate tool definitions."""
        if not tools:
            # Check if this is a modular pack before warning
            if structure and structure.get("tools"):
                return  # Modular pack - tools are in separate files
            self.warnings.append("No tools defined in pack")
            return

        for tool_name, tool in tools.items():
            self._validate_tool(tool_name, tool)

    def _validate_tool(self, tool_name: str, tool) -> None:
        """Validate individual tool."""
        if not tool.description:
            self.errors.append(f"Tool {tool_name}: description is required")

        if not tool.type:
            self.errors.append(f"Tool {tool_name}: type is required")

        # Validate parameters
        param_names = set()
        for param in tool.parameters:
            if param.name in param_names:
                self.errors.append(f"Tool {tool_name}: duplicate parameter name '{param.name}'")
            param_names.add(param.name)

            valid_types = ["string", "integer", "number", "boolean", "array", "object"]
            if param.type not in valid_types:
                self.errors.append(f"Tool {tool_name}: invalid parameter type '{param.type}'")

        # Type-specific validation
        if tool.type.value in ["list", "details", "search", "execute"] and not tool.endpoint:
            self.errors.append(
                f"Tool {tool_name}: endpoint is required for {tool.type.value} tools"
            )

        if tool.type.value == "query" and not tool.sql:
            self.errors.append(f"Tool {tool_name}: sql is required for query tools")

        if tool.type.value == "command" and not tool.command:
            self.errors.append(f"Tool {tool_name}: command is required for command tools")

    def _validate_prompts(self, prompts: Dict[str, Any]) -> None:
        """Validate prompt definitions."""
        for prompt_name, prompt in prompts.items():
            if not prompt.template:
                self.errors.append(f"Prompt {prompt_name}: template is required")

            if not prompt.description:
                self.errors.append(f"Prompt {prompt_name}: description is required")

    def _validate_resources(self, resources: Dict[str, Any]) -> None:
        """Validate resource definitions."""
        for resource_name, resource in resources.items():
            if not resource.url:
                self.errors.append(f"Resource {resource_name}: url is required")

            if not resource.type:
                self.errors.append(f"Resource {resource_name}: type is required")

            valid_types = ["documentation", "api_reference", "tutorial", "example", "support"]
            if resource.type not in valid_types:
                self.warnings.append(f"Resource {resource_name}: unknown type '{resource.type}'")

    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report."""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy(),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


def validate_pack_yaml(yaml_path: str) -> Dict[str, Any]:
    """Validate a pack YAML file.

    Args:
        yaml_path: Path to pack.yaml file

    Returns:
        Validation report dictionary
    """
    try:
        pack = Pack.from_yaml_file(yaml_path)
        validator = PackValidator()
        validator.validate_pack(pack)
        return validator.get_validation_report()
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to load pack: {str(e)}"],
            "warnings": [],
            "error_count": 1,
            "warning_count": 0,
        }


def validate_pack_dict(pack_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pack data from dictionary.

    Args:
        pack_data: Pack configuration as dictionary

    Returns:
        Validation report dictionary
    """
    try:
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        validator.validate_pack(pack)
        return validator.get_validation_report()
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to parse pack: {str(e)}"],
            "warnings": [],
            "error_count": 1,
            "warning_count": 0,
        }


class PackCollectionValidator:
    """Validates collections of knowledge packs."""

    def __init__(self, base_dir: str = "."):
        """Initialize collection validator.

        Args:
            base_dir: Base directory containing packs
        """
        self.base_dir = base_dir
        self.validator = PackValidator()

    def validate_all_packs(self) -> Dict[str, Dict[str, Any]]:
        """Validate all packs in the collection.

        Returns:
            Dictionary mapping pack names to validation results
        """
        from .utils import discover_packs  # Import here to avoid circular imports

        results = {}
        discovered_packs = discover_packs(self.base_dir)

        for pack_info in discovered_packs:
            pack_path = Path(pack_info["path"])
            pack_yaml = pack_path / "pack.yaml"

            if pack_yaml.exists():
                result = validate_pack_yaml(str(pack_yaml))
                result["pack_info"] = pack_info
                results[pack_info["name"]] = result
            else:
                results[pack_info["name"]] = {
                    "valid": False,
                    "errors": ["pack.yaml file not found"],
                    "warnings": [],
                    "error_count": 1,
                    "warning_count": 0,
                    "pack_info": pack_info,
                }

        return results

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary statistics.

        Returns:
            Summary statistics dictionary
        """
        results = self.validate_all_packs()

        total_packs = len(results)
        valid_packs = sum(1 for result in results.values() if result["valid"])
        invalid_packs = total_packs - valid_packs

        total_errors = sum(result.get("error_count", 0) for result in results.values())
        total_warnings = sum(result.get("warning_count", 0) for result in results.values())

        validation_rate = (valid_packs / total_packs * 100) if total_packs > 0 else 0

        return {
            "total_packs": total_packs,
            "valid_packs": valid_packs,
            "invalid_packs": invalid_packs,
            "validation_rate": f"{validation_rate:.1f}%",
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "pack_names": list(results.keys()),
        }

    def print_validation_report(self) -> None:
        """Print a detailed validation report."""
        results = self.validate_all_packs()
        summary = self.get_validation_summary()

        print("=== Pack Collection Validation Report ===")
        print(f"Base Directory: {self.base_dir}")
        print(f"Total Packs: {summary['total_packs']}")
        print(f"Valid: {summary['valid_packs']}")
        print(f"Invalid: {summary['invalid_packs']}")
        print(f"Success Rate: {summary['validation_rate']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Total Warnings: {summary['total_warnings']}")
        print("")

        # Print individual pack results
        for pack_name, result in results.items():
            status = "VALID" if result["valid"] else "INVALID"
            print(f"{status} {pack_name}")

            if result.get("errors"):
                for error in result["errors"]:
                    print(f"  Error: {error}")

            if result.get("warnings"):
                for warning in result["warnings"]:
                    print(f"  Warning: {warning}")

            print()
