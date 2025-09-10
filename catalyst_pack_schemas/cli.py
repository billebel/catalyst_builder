"""Command-line interface for Catalyst Pack Schemas toolkit."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import yaml

from .builder import PackBuilder, PackFactory, create_pack
from .installer import DeploymentOptions, DeploymentTarget, PackInstaller
from .models import Pack
from .utils import create_pack_index, discover_packs, get_pack_statistics, validate_pack_structure
from .validators import PackValidator, validate_pack_yaml


class CLI:
    """Main CLI class for catalyst-pack-schemas toolkit."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            description="Catalyst Pack Schemas - Complete toolkit for building and managing catalyst packs",
            prog="catalyst-packs",
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Create command
        create_parser = subparsers.add_parser("create", help="Create a new pack")
        create_parser.add_argument("name", help="Pack name")
        create_parser.add_argument(
            "--type",
            choices=["rest", "database", "ssh", "monitoring"],
            default="rest",
            help="Pack type",
        )
        create_parser.add_argument("--output", "-o", default=".", help="Output directory")
        create_parser.add_argument("--domain", "-d", default="general", help="Business domain")
        create_parser.add_argument("--vendor", "-v", default="Community", help="Pack vendor")
        create_parser.add_argument("--base-url", help="Base URL for REST API packs")
        create_parser.add_argument("--description", help="Pack description")

        # Validate command
        validate_parser = subparsers.add_parser("validate", help="Validate pack(s)")
        validate_parser.add_argument(
            "path", nargs="?", default=".", help="Path to pack file or directory"
        )
        validate_parser.add_argument("--strict", action="store_true", help="Strict validation mode")
        validate_parser.add_argument("--format", choices=["text", "json"], default="text")
        validate_parser.add_argument(
            "--summary", action="store_true", help="Show only summary statistics"
        )

        # Install command
        install_parser = subparsers.add_parser("install", help="Install a pack")
        install_parser.add_argument("source", help="Pack source (file, directory, or URL)")
        install_parser.add_argument(
            "--target", default="./installed_packs", help="Installation directory"
        )
        install_parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be installed"
        )

        # List command
        list_parser = subparsers.add_parser("list", help="List discovered packs")
        list_parser.add_argument("path", nargs="?", default=".", help="Path to search for packs")
        list_parser.add_argument("--format", choices=["text", "json"], default="text")
        list_parser.add_argument("--stats", action="store_true", help="Show collection statistics")

        # Index command
        index_parser = subparsers.add_parser("index", help="Create pack index file")
        index_parser.add_argument("path", nargs="?", default=".", help="Base directory to index")
        index_parser.add_argument("--output", "-o", default="PACK_INDEX.md", help="Output file")

        # Deploy command
        deploy_parser = subparsers.add_parser("deploy", help="Deploy pack to MCP server")
        deploy_parser.add_argument("pack", help="Pack path or URL to deploy")
        deploy_parser.add_argument(
            "--target", "-t", help="Deployment target (auto-detected if not specified)"
        )
        deploy_parser.add_argument(
            "--mode",
            "-m",
            choices=["development", "staging", "production"],
            default="development",
            help="Deployment mode",
        )
        deploy_parser.add_argument("--env-file", help="Environment file to use")
        deploy_parser.add_argument("--secrets", help="Secrets source (vault://, aws://, file://)")
        deploy_parser.add_argument(
            "--no-validate", action="store_true", help="Skip pack validation"
        )
        deploy_parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
        deploy_parser.add_argument("--hot-reload", action="store_true", help="Enable hot reload")
        deploy_parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be deployed"
        )
        deploy_parser.add_argument(
            "--force", action="store_true", help="Force deployment even if validation fails"
        )

        # Status command
        status_parser = subparsers.add_parser("status", help="Show deployment status")
        status_parser.add_argument("--target", "-t", help="Deployment target to check")
        status_parser.add_argument("--format", choices=["text", "json"], default="text")

        # Rollback command
        rollback_parser = subparsers.add_parser("rollback", help="Rollback pack deployment")
        rollback_parser.add_argument("pack", help="Pack name to rollback")
        rollback_parser.add_argument("--target", "-t", help="Deployment target")
        rollback_parser.add_argument("--to-version", help="Version to rollback to")

        # Uninstall command
        uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall deployed pack")
        uninstall_parser.add_argument("pack", help="Pack name to uninstall")
        uninstall_parser.add_argument("--target", "-t", help="Deployment target")

        # Init command
        init_parser = subparsers.add_parser(
            "init", help="Initialize a pack development environment"
        )
        init_parser.add_argument("--name", help="Project name")
        init_parser.add_argument(
            "--template",
            choices=["basic", "rest-api", "database"],
            default="basic",
            help="Project template",
        )

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        parsed_args = self.parser.parse_args(args)

        if not parsed_args.command:
            self.parser.print_help()
            return 1

        try:
            if parsed_args.command == "create":
                return self._create_pack(parsed_args)
            elif parsed_args.command == "validate":
                return self._validate_pack(parsed_args)
            elif parsed_args.command == "install":
                return self._install_pack(parsed_args)
            elif parsed_args.command == "list":
                return self._list_packs(parsed_args)
            elif parsed_args.command == "index":
                return self._create_index(parsed_args)
            elif parsed_args.command == "deploy":
                return self._deploy_pack(parsed_args)
            elif parsed_args.command == "status":
                return self._show_status(parsed_args)
            elif parsed_args.command == "rollback":
                return self._rollback_pack(parsed_args)
            elif parsed_args.command == "uninstall":
                return self._uninstall_pack(parsed_args)
            elif parsed_args.command == "init":
                return self._init_project(parsed_args)
        except Exception as e:
            print(f"Error: {e}")
            return 1

        return 0

    def _create_pack(self, args) -> int:
        """Create a new pack."""
        print(f"Creating {args.type} pack: {args.name}")

        try:
            pack_dir = create_pack(
                pack_name=args.name,
                output_dir=args.output,
                connection_type=args.type,
                domain=args.domain,
                vendor=args.vendor,
                base_url=args.base_url,
                description=args.description,
            )

            print(f"Created pack '{args.name}' at: {pack_dir}")
            print(f"  Connection type: {args.type}")
            print(f"  Domain: {args.domain}")
            print(f"  Vendor: {args.vendor}")
            print("")
            print("Next steps:")
            print(f"1. Edit {pack_dir}/pack.yaml to configure your connection")
            print(f"2. Add tools in {pack_dir}/tools/")
            print(f"3. Add prompts in {pack_dir}/prompts/")
            print(f"4. Test with: catalyst-packs validate {pack_dir}")

            return 0
        except Exception as e:
            print(f"Failed to create pack: {e}")
            return 1

    def _validate_pack(self, args) -> int:
        """Validate pack(s)."""
        path = Path(args.path)
        validator = PackValidator()
        results = []

        if path.is_file():
            result = self._validate_single_file(path, validator, args.strict)
            results.append(result)
        elif path.is_dir():
            # Look for main pack.yaml file first
            pack_yaml = path / "pack.yaml"
            if pack_yaml.exists():
                result = self._validate_single_file(pack_yaml, validator, args.strict)
                results.append(result)
            else:
                # If no pack.yaml, validate all YAML files in the root directory only
                for pack_file in path.glob("*.yaml"):
                    if pack_file.name.startswith("."):
                        continue
                    result = self._validate_single_file(pack_file, validator, args.strict)
                    results.append(result)
        else:
            print(f"Error: Path {path} does not exist")
            return 1

        if not results:
            print("No pack files found to validate")
            return 1

        # Output results
        if args.format == "json":
            print(json.dumps([r.__dict__ for r in results], indent=2))
        else:
            self._print_validation_results(results)

        # Return error if any validation failed
        return 0 if all(r.is_valid for r in results) else 1

    def _validate_single_file(self, file_path: Path, validator: PackValidator, strict: bool):
        """Validate a single pack file."""
        try:
            # Use the standalone validate_pack_yaml function
            validation_result = validate_pack_yaml(str(file_path))

            # Create a result object that matches the expected interface
            class ValidationResult:
                def __init__(self, file_path, result_dict):
                    self.file_path = file_path
                    self.is_valid = result_dict.get("valid", False)
                    self.errors = result_dict.get("errors", [])
                    self.warnings = result_dict.get("warnings", [])

            return ValidationResult(str(file_path), validation_result)
        except Exception as e:
            # Create a failed result
            class FailedResult:
                def __init__(self, file_path, error):
                    self.file_path = file_path
                    self.is_valid = False
                    self.errors = [str(error)]
                    self.warnings = []

            return FailedResult(str(file_path), e)

    def _print_validation_results(self, results):
        """Print validation results in text format."""
        total = len(results)
        passed = sum(1 for r in results if r.is_valid)
        failed = total - passed

        print(f"\nValidation Results:")
        print(f"==================")
        print(f"Total: {total}, Passed: {passed}, Failed: {failed}\n")

        for result in results:
            status = "PASS" if result.is_valid else "FAIL"
            print(f"{status} {result.file_path}")

            if not result.is_valid and hasattr(result, "errors"):
                for error in result.errors:
                    print(f"  Error: {error}")

            if hasattr(result, "warnings") and result.warnings:
                for warning in result.warnings:
                    print(f"  Warning: {warning}")
            print()

    def _install_pack(self, args) -> int:
        """Install a pack."""
        installer = PackInstaller(args.target)

        if args.dry_run:
            print(f"Dry run: Would install {args.source} to {args.target}")
            return 0

        try:
            installer.install(args.source)
            print(f"Pack installed successfully to {args.target}")
            return 0
        except Exception as e:
            print(f"Installation failed: {e}")
            return 1

    def _list_packs(self, args) -> int:
        """List installed packs."""
        installer = PackInstaller(args.target)
        packs = installer.list_installed()

        if args.format == "json":
            print(json.dumps([p.__dict__ for p in packs], indent=2))
        else:
            if not packs:
                print("No packs installed")
            else:
                print(f"Installed packs in {args.target}:")
                for pack in packs:
                    print(f"  - {pack.name} ({pack.version}): {pack.description}")

        return 0

    def _init_project(self, args) -> int:
        """Initialize a pack development project."""
        name = args.name or Path.cwd().name

        print(f"Initializing pack development project: {name}")

        # Create project structure
        project_dir = Path(name)
        project_dir.mkdir(exist_ok=True)

        # Create example pack based on template
        if args.template == "rest-api":
            builder = PackFactory.create_rest_api_pack(
                f"{name}-api", "https://api.example.com", f"REST API integration for {name}"
            )
        elif args.template == "database":
            builder = PackFactory.create_database_pack(f"{name}-db")
        else:
            builder = PackBuilder(name)
            builder.set_metadata(description=f"Basic pack for {name}", tags=["example", "template"])

        # Scaffold the pack
        builder.scaffold(str(project_dir))

        # Create additional project files
        gitignore_content = """
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.env
.DS_Store
*.egg-info/
dist/
build/
.pytest_cache/
"""

        with open(project_dir / ".gitignore", "w") as f:
            f.write(gitignore_content.strip())

        readme_content = f"""# {name} Pack

This is a Catalyst pack for {name} integration.

## Development

1. Install the catalyst-pack-schemas toolkit:
   ```bash
   pip install catalyst-pack-schemas
   ```

2. Validate your pack:
   ```bash
   catalyst-packs validate {name}/pack.yaml
   ```

3. Install your pack:
   ```bash
   catalyst-packs install {name}/
   ```

## Pack Structure

- `pack.yaml` - Main pack definition
- `tools/` - Tool definitions (if modular)
- `prompts/` - Prompt templates
- `README.md` - Documentation

## Contributing

1. Make changes to your pack
2. Validate with `catalyst-packs validate`
3. Test your changes
4. Submit a pull request
"""

        with open(project_dir / "README.md", "w") as f:
            f.write(readme_content)

        print(f"Project '{name}' initialized successfully")
        print(f"Created in: {project_dir.absolute()}")
        print(f"\nNext steps:")
        print(f"  cd {name}")
        print(f"  catalyst-packs validate {name}/pack.yaml")

        return 0

    def _list_packs(self, args) -> int:
        """List discovered packs."""
        try:
            discovered = discover_packs(args.path)

            if args.stats:
                stats = get_pack_statistics(args.path)
                if args.format == "json":
                    print(json.dumps(stats, indent=2))
                else:
                    print(f"Pack Collection Statistics ({args.path})")
                    print("=" * 50)
                    print(f"Total packs: {stats['total_packs']}")
                    print(f"Domains: {', '.join(stats['domains'].keys())}")
                    print(f"Connection types: {', '.join(stats['connection_types'].keys())}")
                    print(f"Vendors: {', '.join(stats['vendors'].keys())}")
            else:
                if args.format == "json":
                    print(json.dumps(discovered, indent=2))
                else:
                    if not discovered:
                        print(f"No packs found in {args.path}")
                        return 1

                    print(f"Discovered Packs ({len(discovered)})")
                    print("=" * 50)
                    for pack in discovered:
                        print(f"{pack['name']} (v{pack['version']})")
                        print(f"   Domain: {pack['domain']}")
                        print(f"   Vendor: {pack['vendor']}")
                        print(f"   Type: {pack['connection_type']}")
                        print(f"   Path: {pack['path']}")
                        print()

            return 0
        except Exception as e:
            print(f"Error listing packs: {e}")
            return 1

    def _create_index(self, args) -> int:
        """Create pack index file."""
        try:
            create_pack_index(args.path, args.output)
            print(f"Pack index created: {args.output}")
            return 0
        except Exception as e:
            print(f"Error creating index: {e}")
            return 1

    def _deploy_pack(self, args) -> int:
        """Deploy pack to MCP server."""
        print("WARNING: Deployment functionality is under development")
        print("   This will integrate with MCP server deployment in a future release")
        print(f"   Pack to deploy: {args.pack}")
        print(f"   Target: {args.target or 'auto-detect'}")
        print(f"   Mode: {args.mode}")

        # For now, just show what would be deployed
        if args.dry_run:
            print("Dry run - showing planned deployment:")

        return 0

    def _show_status(self, args) -> int:
        """Show deployment status."""
        print("WARNING: Status functionality is under development")
        print("   This will show MCP server deployment status in a future release")
        print(f"   Target: {args.target or 'all targets'}")

        return 0

    def _rollback_pack(self, args) -> int:
        """Rollback pack deployment."""
        print("WARNING: Rollback functionality is under development")
        print("   This will rollback MCP server deployments in a future release")
        print(f"   Pack: {args.pack}")
        print(f"   Target: {args.target or 'auto-detect'}")
        print(f"   To version: {args.to_version or 'previous'}")

        return 0

    def _uninstall_pack(self, args) -> int:
        """Uninstall deployed pack."""
        print("WARNING: Uninstall functionality is under development")
        print("   This will uninstall from MCP servers in a future release")
        print(f"   Pack: {args.pack}")
        print(f"   Target: {args.target or 'auto-detect'}")

        return 0


def main():
    """Main CLI entry point."""
    cli = CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
