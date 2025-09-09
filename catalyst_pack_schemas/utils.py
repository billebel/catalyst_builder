"""
Collection management utilities for discovering and managing groups of packs.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import Pack
from .validators import validate_pack_yaml


def discover_packs(base_dir: str = ".") -> List[Dict[str, Any]]:
    """Discover all knowledge packs in a directory structure.

    Args:
        base_dir: Base directory to search for packs

    Returns:
        List of pack information dictionaries
    """
    base_path = Path(base_dir)
    discovered_packs = []

    # Search in common pack directories
    search_dirs = [
        base_path / "production",
        base_path / "development",
        base_path / "examples",
        base_path,  # Also search root
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for item in search_dir.iterdir():
            if not item.is_dir() or item.name.startswith("."):
                continue

            # Skip system directories when scanning root
            if search_dir == base_path and item.name in [
                "catalyst_pack_schemas",
                "schemas",
                "tests",
                ".git",
                "__pycache__",
                "dist",
                "docs",
                "examples",
            ]:
                continue

            pack_yaml = item / "pack.yaml"
            if pack_yaml.exists():
                try:
                    with open(pack_yaml, "r") as f:
                        pack_data = yaml.safe_load(f)

                    pack_info = {
                        "name": pack_data.get("metadata", {}).get("name", item.name),
                        "path": str(item),
                        "version": pack_data.get("metadata", {}).get("version", "unknown"),
                        "domain": pack_data.get("metadata", {}).get("domain", "unknown"),
                        "vendor": pack_data.get("metadata", {}).get("vendor", "unknown"),
                        "connection_type": pack_data.get("connection", {}).get("type", "unknown"),
                        "category": search_dir.name if search_dir != base_path else "root",
                    }

                    discovered_packs.append(pack_info)

                except Exception as e:
                    print(f"Warning: Could not parse {pack_yaml}: {e}")

    return discovered_packs


def load_pack_collection(base_dir: str = ".") -> Dict[str, Pack]:
    """Load all valid packs from a directory structure.

    Args:
        base_dir: Base directory containing packs

    Returns:
        Dictionary mapping pack names to Pack objects
    """
    pack_collection = {}
    discovered = discover_packs(base_dir)

    for pack_info in discovered:
        pack_yaml = Path(pack_info["path"]) / "pack.yaml"

        try:
            pack = Pack.from_yaml_file(str(pack_yaml))
            pack_collection[pack_info["name"]] = pack
        except Exception as e:
            print(f"Warning: Could not load pack {pack_info['name']}: {e}")

    return pack_collection


def get_pack_statistics(base_dir: str = ".") -> Dict[str, Any]:
    """Get statistics about the pack collection.

    Args:
        base_dir: Base directory containing packs

    Returns:
        Statistics dictionary
    """
    discovered = discover_packs(base_dir)

    # Count by category
    categories = {}
    domains = {}
    connection_types = {}
    vendors = {}

    for pack in discovered:
        # Count categories
        category = pack["category"]
        categories[category] = categories.get(category, 0) + 1

        # Count domains
        domain = pack["domain"]
        domains[domain] = domains.get(domain, 0) + 1

        # Count connection types
        conn_type = pack["connection_type"]
        connection_types[conn_type] = connection_types.get(conn_type, 0) + 1

        # Count vendors
        vendor = pack["vendor"]
        vendors[vendor] = vendors.get(vendor, 0) + 1

    return {
        "total_packs": len(discovered),
        "categories": categories,
        "domains": domains,
        "connection_types": connection_types,
        "vendors": vendors,
        "pack_list": [pack["name"] for pack in discovered],
    }


def create_pack_index(base_dir: str = ".", output_file: str = "PACK_INDEX.md") -> None:
    """Create a markdown index of all packs.

    Args:
        base_dir: Base directory containing packs
        output_file: Output file for the index
    """
    discovered = discover_packs(base_dir)
    stats = get_pack_statistics(base_dir)

    content = ["# Catalyst Knowledge Packs Index", ""]
    content.append(f"**Total Packs:** {stats['total_packs']}")
    content.append("")

    # Summary by category
    content.append("## Categories")
    for category, count in stats["categories"].items():
        content.append(f"- **{category}**: {count} packs")
    content.append("")

    # Summary by domain
    content.append("## Domains")
    for domain, count in stats["domains"].items():
        content.append(f"- **{domain}**: {count} packs")
    content.append("")

    # Summary by connection type
    content.append("## Connection Types")
    for conn_type, count in stats["connection_types"].items():
        content.append(f"- **{conn_type}**: {count} packs")
    content.append("")

    # Detailed pack list
    content.append("## Pack Details")
    content.append("")

    # Group by category
    for category in stats["categories"].keys():
        category_packs = [p for p in discovered if p["category"] == category]
        if category_packs:
            content.append(f"### {category.title()} Packs")
            content.append("")

            for pack in category_packs:
                content.append(f"#### {pack['name']}")
                content.append(f"- **Version:** {pack['version']}")
                content.append(f"- **Domain:** {pack['domain']}")
                content.append(f"- **Vendor:** {pack['vendor']}")
                content.append(f"- **Connection:** {pack['connection_type']}")
                content.append(f"- **Path:** `{pack['path']}`")
                content.append("")

    # Write index file
    with open(Path(base_dir) / output_file, "w") as f:
        f.write("\n".join(content))

    print(f"Pack index created: {output_file}")


def export_pack_metadata(base_dir: str = ".", output_file: str = "pack_metadata.json") -> None:
    """Export pack metadata to JSON for programmatic use.

    Args:
        base_dir: Base directory containing packs
        output_file: Output JSON file
    """
    discovered = discover_packs(base_dir)
    stats = get_pack_statistics(base_dir)

    export_data = {"generated_at": str(Path().resolve()), "statistics": stats, "packs": discovered}

    with open(Path(base_dir) / output_file, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"Pack metadata exported: {output_file}")


def validate_pack_structure(pack_dir: str) -> Dict[str, Any]:
    """Validate the structure of a pack directory.

    Args:
        pack_dir: Path to pack directory

    Returns:
        Validation result dictionary
    """
    pack_path = Path(pack_dir)
    result = {"valid": True, "errors": [], "warnings": [], "structure_info": {}}

    # Check required files
    pack_yaml = pack_path / "pack.yaml"
    if not pack_yaml.exists():
        result["valid"] = False
        result["errors"].append("Missing pack.yaml file")
        return result

    # Check for modular structure
    modular_dirs = ["tools", "prompts", "resources", "transforms"]
    modular_structure = any((pack_path / d).exists() for d in modular_dirs)

    result["structure_info"]["modular"] = modular_structure
    result["structure_info"]["directories"] = []

    for d in modular_dirs:
        dir_path = pack_path / d
        if dir_path.exists():
            result["structure_info"]["directories"].append(d)

            # Check for YAML files in each directory
            yaml_files = list(dir_path.glob("*.yaml"))
            if not yaml_files:
                result["warnings"].append(f"Directory {d}/ exists but contains no YAML files")

    # Validate pack.yaml content using the validator
    try:
        pack_validation = validate_pack_yaml(str(pack_yaml))
        if hasattr(pack_validation, "is_valid"):
            result["valid"] = result["valid"] and pack_validation.is_valid
            if hasattr(pack_validation, "errors"):
                result["errors"].extend(pack_validation.errors or [])
            if hasattr(pack_validation, "warnings"):
                result["warnings"].extend(pack_validation.warnings or [])
        else:
            # Handle different return format
            if isinstance(pack_validation, dict):
                result["valid"] = result["valid"] and pack_validation.get("valid", False)
                result["errors"].extend(pack_validation.get("errors", []))
                result["warnings"].extend(pack_validation.get("warnings", []))
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Pack validation error: {str(e)}")

    return result
