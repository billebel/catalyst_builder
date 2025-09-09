"""Pack installation and management utilities."""

import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import requests
import yaml

from .models import PackMetadata
from .validators import PackValidator

logger = logging.getLogger(__name__)


@dataclass
class DeploymentTarget:
    """Deployment target configuration."""

    type: str  # local, ssh, docker, http, git
    location: str  # path, url, container, etc.
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class DeploymentOptions:
    """Deployment options and settings."""

    mode: str = "development"  # development, staging, production
    validate: bool = True
    backup: bool = True
    hot_reload: bool = False
    env_file: Optional[str] = None
    secrets_source: Optional[str] = None
    dry_run: bool = False
    force: bool = False


class BaseDeploymentHandler:
    """Base class for deployment target handlers."""

    def __init__(self, target: DeploymentTarget, options: DeploymentOptions):
        self.target = target
        self.options = options
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def deploy(self, pack_source: Path, pack_name: str) -> Dict[str, Any]:
        """Deploy a pack to the target."""
        raise NotImplementedError("Subclasses must implement deploy method")

    def status(self) -> Dict[str, Any]:
        """Get deployment status."""
        raise NotImplementedError("Subclasses must implement status method")

    def rollback(self, pack_name: str, to_version: Optional[str] = None) -> Dict[str, Any]:
        """Rollback a deployment."""
        raise NotImplementedError("Subclasses must implement rollback method")

    def uninstall(self, pack_name: str) -> Dict[str, Any]:
        """Uninstall a deployed pack."""
        raise NotImplementedError("Subclasses must implement uninstall method")

    def _create_deployment_metadata(
        self, pack_name: str, version: str, files: List[str]
    ) -> Dict[str, Any]:
        """Create deployment metadata."""
        return {
            "pack_name": pack_name,
            "version": version,
            "deployed_at": datetime.now().isoformat(),
            "mode": self.options.mode,
            "files": files,
            "target_type": self.target.type,
            "target_location": self.target.location,
        }


class LocalDeploymentHandler(BaseDeploymentHandler):
    """Handler for local filesystem deployments."""

    def deploy(self, pack_source: Path, pack_name: str) -> Dict[str, Any]:
        """Deploy pack to local filesystem."""
        try:
            target_dir = Path(self.target.location)
            pack_target_dir = target_dir / pack_name

            # Create target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)

            # Handle dry run
            if self.options.dry_run:
                return {
                    "success": True,
                    "pack_name": pack_name,
                    "target_path": str(pack_target_dir),
                    "mode": self.options.mode,
                    "dry_run": True,
                    "message": f"Would deploy {pack_name} to {pack_target_dir}",
                }

            # Backup existing deployment if requested
            if self.options.backup and pack_target_dir.exists():
                backup_path = self._create_backup(pack_target_dir)
                self.logger.info(f"Created backup at {backup_path}")

            # Validate pack if requested
            if self.options.validate:
                validation_result = self._validate_pack(pack_source)
                if not validation_result["valid"] and not self.options.force:
                    return {
                        "success": False,
                        "error": "Pack validation failed",
                        "validation_errors": validation_result["errors"],
                    }

            # Copy pack files
            if pack_target_dir.exists() and not self.options.force:
                shutil.rmtree(pack_target_dir)

            shutil.copytree(pack_source, pack_target_dir, dirs_exist_ok=True)

            # Handle environment files
            self._handle_environment_files(pack_source, pack_target_dir)

            # Create deployment metadata
            files = [
                str(f.relative_to(pack_target_dir))
                for f in pack_target_dir.rglob("*")
                if f.is_file()
            ]
            pack_version = self._get_pack_version(pack_source)

            metadata = self._create_deployment_metadata(pack_name, pack_version, files)
            metadata_file = pack_target_dir / ".catalyst_deployment.json"

            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            self.logger.info(f"Successfully deployed {pack_name} to {pack_target_dir}")

            return {
                "success": True,
                "pack_name": pack_name,
                "version": pack_version,
                "target_path": str(pack_target_dir),
                "mode": self.options.mode,
                "files_deployed": len(files),
                "deployed_at": metadata["deployed_at"],
            }

        except Exception as e:
            self.logger.error(f"Deployment failed: {str(e)}")
            return {
                "success": False,
                "error": f"Deployment failed: {str(e)}",
                "pack_name": pack_name,
            }

    def status(self) -> Dict[str, Any]:
        """Get status of local deployments."""
        try:
            target_dir = Path(self.target.location)
            if not target_dir.exists():
                return {
                    "target": str(target_dir),
                    "packs": [],
                    "message": "Target directory does not exist",
                }

            packs = []
            for item in target_dir.iterdir():
                if item.is_dir():
                    metadata_file = item / ".catalyst_deployment.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file) as f:
                                metadata = json.load(f)
                            packs.append(metadata)
                        except Exception as e:
                            self.logger.warning(f"Could not read metadata for {item.name}: {e}")
                            packs.append(
                                {
                                    "pack_name": item.name,
                                    "version": "unknown",
                                    "status": "metadata_error",
                                    "error": str(e),
                                }
                            )

            return {"target": str(target_dir), "packs": packs, "total_packs": len(packs)}

        except Exception as e:
            return {
                "target": str(self.target.location),
                "error": f"Status check failed: {str(e)}",
                "packs": [],
            }

    def rollback(self, pack_name: str, to_version: Optional[str] = None) -> Dict[str, Any]:
        """Rollback a local deployment."""
        try:
            target_dir = Path(self.target.location)
            pack_dir = target_dir / pack_name

            if not pack_dir.exists():
                return {"success": False, "error": f"Pack {pack_name} not found at target location"}

            # Find backup to restore
            backup_dir = target_dir / f".{pack_name}_backups"
            if not backup_dir.exists():
                return {"success": False, "error": f"No backups found for {pack_name}"}

            # Get the most recent backup or specific version
            backups = sorted(backup_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)

            if not backups:
                return {"success": False, "error": f"No backup files found for {pack_name}"}

            # Select backup to restore
            backup_to_restore = backups[0]  # Most recent by default
            if to_version:
                version_backups = [b for b in backups if to_version in b.name]
                if version_backups:
                    backup_to_restore = version_backups[0]
                else:
                    return {"success": False, "error": f"No backup found for version {to_version}"}

            # Perform rollback
            if pack_dir.exists():
                temp_dir = target_dir / f".{pack_name}_temp"
                shutil.move(pack_dir, temp_dir)

            shutil.copytree(backup_to_restore, pack_dir)

            # Clean up temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            return {
                "success": True,
                "pack_name": pack_name,
                "restored_from": str(backup_to_restore),
                "message": f"Successfully rolled back {pack_name}",
            }

        except Exception as e:
            return {"success": False, "error": f"Rollback failed: {str(e)}", "pack_name": pack_name}

    def uninstall(self, pack_name: str) -> Dict[str, Any]:
        """Uninstall a local deployment."""
        try:
            target_dir = Path(self.target.location)
            pack_dir = target_dir / pack_name

            if not pack_dir.exists():
                return {"success": False, "error": f"Pack {pack_name} not found at target location"}

            # Create final backup before uninstall
            if self.options.backup:
                backup_path = self._create_backup(pack_dir, suffix="_uninstall")
                self.logger.info(f"Created final backup at {backup_path}")

            # Remove pack directory
            shutil.rmtree(pack_dir)

            return {
                "success": True,
                "pack_name": pack_name,
                "message": f"Successfully uninstalled {pack_name}",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Uninstall failed: {str(e)}",
                "pack_name": pack_name,
            }

    def _create_backup(self, pack_dir: Path, suffix: str = "") -> Path:
        """Create a backup of the pack directory."""
        target_dir = pack_dir.parent
        backup_base_dir = target_dir / f".{pack_dir.name}_backups"
        backup_base_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{pack_dir.name}_{timestamp}{suffix}"
        backup_path = backup_base_dir / backup_name

        shutil.copytree(pack_dir, backup_path)
        return backup_path

    def _validate_pack(self, pack_source: Path) -> Dict[str, Any]:
        """Validate pack before deployment."""
        try:
            from .validators import validate_pack_yaml

            pack_yaml = pack_source / "pack.yaml"
            if pack_yaml.exists():
                return validate_pack_yaml(str(pack_yaml))
            else:
                return {
                    "valid": False,
                    "errors": ["pack.yaml not found"],
                    "warnings": [],
                    "error_count": 1,
                    "warning_count": 0,
                }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "error_count": 1,
                "warning_count": 0,
            }

    def _get_pack_version(self, pack_source: Path) -> str:
        """Get pack version from pack.yaml."""
        try:
            pack_yaml = pack_source / "pack.yaml"
            if pack_yaml.exists():
                with open(pack_yaml) as f:
                    pack_data = yaml.safe_load(f)
                return pack_data.get("metadata", {}).get("version", "1.0.0")
            return "1.0.0"
        except Exception:
            return "1.0.0"

    def _handle_environment_files(self, pack_source: Path, pack_target: Path):
        """Handle environment file deployment."""
        if self.options.env_file:
            env_file = Path(self.options.env_file)
            if env_file.exists():
                target_env = pack_target / ".env"
                shutil.copy2(env_file, target_env)
                self.logger.info(f"Deployed custom environment file to {target_env}")
        elif (pack_source / ".env").exists():
            # Copy default .env if it exists
            shutil.copy2(pack_source / ".env", pack_target / ".env")


class DockerDeploymentHandler(BaseDeploymentHandler):
    """Handler for Docker container deployments."""

    def deploy(self, pack_source: Path, pack_name: str) -> Dict[str, Any]:
        """Deploy pack to Docker container."""
        try:
            container_name = self.target.location

            # Check if Docker is available
            if not self._check_docker():
                return {"success": False, "error": "Docker is not available or not running"}

            # Check if container exists
            if not self._container_exists(container_name):
                return {"success": False, "error": f"Container {container_name} not found"}

            if self.options.dry_run:
                return {
                    "success": True,
                    "pack_name": pack_name,
                    "container": container_name,
                    "mode": self.options.mode,
                    "dry_run": True,
                    "message": f"Would deploy {pack_name} to container {container_name}",
                }

            # Validate pack if requested
            if self.options.validate:
                validation_result = self._validate_pack(pack_source)
                if not validation_result["valid"] and not self.options.force:
                    return {
                        "success": False,
                        "error": "Pack validation failed",
                        "validation_errors": validation_result["errors"],
                    }

            # Create temporary archive
            with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as tmp_file:
                archive_path = tmp_file.name

            try:
                # Create tar archive of pack
                subprocess.run(
                    ["tar", "-cf", archive_path, "-C", str(pack_source.parent), pack_source.name],
                    check=True,
                    capture_output=True,
                )

                # Copy to container
                container_path = self.target.config.get("pack_dir", "/app/knowledge-packs")
                subprocess.run(
                    [
                        "docker",
                        "cp",
                        archive_path,
                        f"{container_name}:{container_path}/{pack_name}.tar",
                    ],
                    check=True,
                    capture_output=True,
                )

                # Extract in container
                extract_cmd = (
                    f"cd {container_path} && tar -xf {pack_name}.tar && rm {pack_name}.tar"
                )
                subprocess.run(
                    ["docker", "exec", container_name, "sh", "-c", extract_cmd],
                    check=True,
                    capture_output=True,
                )

                # Create deployment metadata in container
                pack_version = self._get_pack_version(pack_source)
                metadata = self._create_deployment_metadata(pack_name, pack_version, [])

                metadata_json = json.dumps(metadata)
                metadata_cmd = f"echo '{metadata_json}' > {container_path}/{pack_name}/.catalyst_deployment.json"
                subprocess.run(
                    ["docker", "exec", container_name, "sh", "-c", metadata_cmd],
                    check=True,
                    capture_output=True,
                )

                return {
                    "success": True,
                    "pack_name": pack_name,
                    "version": pack_version,
                    "container": container_name,
                    "container_path": f"{container_path}/{pack_name}",
                    "mode": self.options.mode,
                    "deployed_at": metadata["deployed_at"],
                }

            finally:
                # Clean up temporary archive
                if os.path.exists(archive_path):
                    os.unlink(archive_path)

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Docker command failed: {e.stderr.decode() if e.stderr else str(e)}",
                "pack_name": pack_name,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Docker deployment failed: {str(e)}",
                "pack_name": pack_name,
            }

    def status(self) -> Dict[str, Any]:
        """Get status of Docker deployments."""
        try:
            container_name = self.target.location

            if not self._check_docker() or not self._container_exists(container_name):
                return {
                    "container": container_name,
                    "error": "Container not available",
                    "packs": [],
                }

            # List deployed packs
            container_path = self.target.config.get("pack_dir", "/app/knowledge-packs")
            result = subprocess.run(
                ["docker", "exec", container_name, "ls", "-la", container_path],
                capture_output=True,
                text=True,
                check=True,
            )

            packs = []
            for line in result.stdout.split("\n")[1:]:  # Skip first line (total)
                if line.strip() and not line.startswith("total"):
                    parts = line.split()
                    if len(parts) >= 9 and parts[0].startswith("d"):  # Directory
                        pack_name = parts[-1]
                        if not pack_name.startswith("."):
                            # Try to get metadata
                            try:
                                metadata_cmd = (
                                    f"cat {container_path}/{pack_name}/.catalyst_deployment.json"
                                )
                                metadata_result = subprocess.run(
                                    ["docker", "exec", container_name, "sh", "-c", metadata_cmd],
                                    capture_output=True,
                                    text=True,
                                    check=True,
                                )

                                metadata = json.loads(metadata_result.stdout)
                                packs.append(metadata)
                            except:
                                packs.append(
                                    {
                                        "pack_name": pack_name,
                                        "version": "unknown",
                                        "status": "metadata_missing",
                                    }
                                )

            return {
                "container": container_name,
                "container_path": container_path,
                "packs": packs,
                "total_packs": len(packs),
            }

        except Exception as e:
            return {
                "container": self.target.location,
                "error": f"Status check failed: {str(e)}",
                "packs": [],
            }

    def rollback(self, pack_name: str, to_version: Optional[str] = None) -> Dict[str, Any]:
        """Rollback Docker deployment (placeholder - would need backup strategy)."""
        return {
            "success": False,
            "error": "Docker rollback not implemented - would require backup strategy",
            "pack_name": pack_name,
        }

    def uninstall(self, pack_name: str) -> Dict[str, Any]:
        """Uninstall from Docker container."""
        try:
            container_name = self.target.location
            container_path = self.target.config.get("pack_dir", "/app/knowledge-packs")

            # Remove pack directory
            remove_cmd = f"rm -rf {container_path}/{pack_name}"
            subprocess.run(
                ["docker", "exec", container_name, "sh", "-c", remove_cmd],
                check=True,
                capture_output=True,
            )

            return {
                "success": True,
                "pack_name": pack_name,
                "container": container_name,
                "message": f"Successfully uninstalled {pack_name} from container",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Docker uninstall failed: {str(e)}",
                "pack_name": pack_name,
            }

    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            return True
        except:
            return False

    def _container_exists(self, container_name: str) -> bool:
        """Check if container exists and is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True,
            )

            return container_name in result.stdout.split("\n")
        except:
            return False

    def _validate_pack(self, pack_source: Path) -> Dict[str, Any]:
        """Validate pack before deployment."""
        try:
            from .validators import validate_pack_yaml

            pack_yaml = pack_source / "pack.yaml"
            if pack_yaml.exists():
                return validate_pack_yaml(str(pack_yaml))
            else:
                return {
                    "valid": False,
                    "errors": ["pack.yaml not found"],
                    "warnings": [],
                    "error_count": 1,
                    "warning_count": 0,
                }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "error_count": 1,
                "warning_count": 0,
            }

    def _get_pack_version(self, pack_source: Path) -> str:
        """Get pack version from pack.yaml."""
        try:
            pack_yaml = pack_source / "pack.yaml"
            if pack_yaml.exists():
                with open(pack_yaml) as f:
                    pack_data = yaml.safe_load(f)
                return pack_data.get("metadata", {}).get("version", "1.0.0")
            return "1.0.0"
        except Exception:
            return "1.0.0"


class InstalledPack:
    """Represents an installed pack."""

    def __init__(self, name: str, version: str, description: str, path: str):
        self.name = name
        self.version = version
        self.description = description
        self.path = path


class MCPInstaller:
    """MCP Pack Installer supporting deployment to various targets."""

    def __init__(self):
        """Initialize MCP installer."""
        self.supported_targets = {
            "local": "LocalTarget",
            "ssh": "SSHTarget",
            "docker": "DockerTarget",
            "http": "HTTPTarget",
            "git": "GitTarget",
        }
        self.deployment_history = []

    def deploy(
        self,
        pack_source: Union[str, Path],
        target: Optional[Union[str, DeploymentTarget]] = None,
        options: Optional[DeploymentOptions] = None,
    ) -> Dict[str, Any]:
        """Deploy a pack to an MCP server.

        Args:
            pack_source: Path to pack or git URL
            target: Deployment target (auto-detected if None)
            options: Deployment options

        Returns:
            Deployment result with status and details
        """
        if options is None:
            options = DeploymentOptions()

        try:
            # Convert pack source to Path
            pack_path = Path(pack_source)

            # Auto-detect target if not provided
            if target is None:
                target = self._auto_detect_target()

            # Convert string target to DeploymentTarget
            if isinstance(target, str):
                target = self._parse_target_string(target)

            # Get pack name
            pack_name = self._get_pack_name(pack_path)

            # Get appropriate handler
            handler = self._get_deployment_handler(target, options)

            # Record deployment attempt
            deployment_record = {
                "pack_source": str(pack_source),
                "pack_name": pack_name,
                "target": asdict(target),
                "options": asdict(options),
                "timestamp": datetime.now().isoformat(),
                "status": "started",
            }
            self.deployment_history.append(deployment_record)

            # Perform deployment
            result = handler.deploy(pack_path, pack_name)

            # Update deployment record
            deployment_record["status"] = "success" if result["success"] else "failed"
            deployment_record["result"] = result

            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Deployment failed: {str(e)}",
                "pack_source": str(pack_source),
                "target": str(target) if target else None,
            }

            # Update deployment history
            if hasattr(self, "deployment_history") and self.deployment_history:
                self.deployment_history[-1]["status"] = "error"
                self.deployment_history[-1]["result"] = error_result

            return error_result

    def status(self, target: Optional[Union[str, DeploymentTarget]] = None) -> Dict[str, Any]:
        """Get status of deployed packs."""
        try:
            # Auto-detect target if not provided
            if target is None:
                target = self._auto_detect_target()

            # Convert string target to DeploymentTarget
            if isinstance(target, str):
                target = self._parse_target_string(target)

            # Get appropriate handler
            handler = self._get_deployment_handler(target, DeploymentOptions())

            return handler.status()

        except Exception as e:
            return {
                "target": str(target) if target else None,
                "error": f"Status check failed: {str(e)}",
                "packs": [],
            }

    def rollback(
        self,
        pack_name: str,
        target: Optional[Union[str, DeploymentTarget]] = None,
        to_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rollback a pack deployment."""
        try:
            # Auto-detect target if not provided
            if target is None:
                target = self._auto_detect_target()

            # Convert string target to DeploymentTarget
            if isinstance(target, str):
                target = self._parse_target_string(target)

            # Get appropriate handler
            handler = self._get_deployment_handler(target, DeploymentOptions())

            return handler.rollback(pack_name, to_version)

        except Exception as e:
            return {
                "success": False,
                "error": f"Rollback failed: {str(e)}",
                "pack_name": pack_name,
                "target": str(target) if target else None,
            }

    def uninstall(
        self, pack_name: str, target: Optional[Union[str, DeploymentTarget]] = None
    ) -> Dict[str, Any]:
        """Uninstall a deployed pack."""
        try:
            # Auto-detect target if not provided
            if target is None:
                target = self._auto_detect_target()

            # Convert string target to DeploymentTarget
            if isinstance(target, str):
                target = self._parse_target_string(target)

            # Get appropriate handler
            handler = self._get_deployment_handler(target, DeploymentOptions())

            return handler.uninstall(pack_name)

        except Exception as e:
            return {
                "success": False,
                "error": f"Uninstall failed: {str(e)}",
                "pack_name": pack_name,
                "target": str(target) if target else None,
            }

    def _auto_detect_target(self) -> DeploymentTarget:
        """Auto-detect deployment target."""
        # Check for common MCP server locations
        common_paths = [
            "./knowledge-packs",
            "./mcp/knowledge-packs",
            "../mcp/knowledge-packs",
            "/app/knowledge-packs",
            "/opt/mcp/knowledge-packs",
        ]

        for path in common_paths:
            if Path(path).exists():
                return DeploymentTarget(type="local", location=path)

        # Default to current directory
        return DeploymentTarget(type="local", location="./knowledge-packs")

    def _parse_target_string(self, target_str: str) -> DeploymentTarget:
        """Parse target string into DeploymentTarget."""
        if target_str.startswith("docker:"):
            container_name = target_str[7:]  # Remove 'docker:' prefix
            return DeploymentTarget(
                type="docker", location=container_name, config={"pack_dir": "/app/knowledge-packs"}
            )
        elif target_str.startswith("ssh:"):
            ssh_spec = target_str[4:]  # Remove 'ssh:' prefix
            return DeploymentTarget(
                type="ssh", location=ssh_spec, config={"remote_path": "/opt/mcp/knowledge-packs"}
            )
        elif target_str.startswith("http:") or target_str.startswith("https:"):
            return DeploymentTarget(type="http", location=target_str)
        else:
            # Assume it's a local path
            return DeploymentTarget(type="local", location=target_str)

    def _get_pack_name(self, pack_path: Path) -> str:
        """Get pack name from path or pack.yaml."""
        if pack_path.is_file():
            pack_path = pack_path.parent

        # Try to get name from pack.yaml
        pack_yaml = pack_path / "pack.yaml"
        if pack_yaml.exists():
            try:
                with open(pack_yaml) as f:
                    pack_data = yaml.safe_load(f)
                return pack_data.get("metadata", {}).get("name", pack_path.name)
            except:
                pass

        return pack_path.name

    def _get_deployment_handler(
        self, target: DeploymentTarget, options: DeploymentOptions
    ) -> BaseDeploymentHandler:
        """Get appropriate deployment handler for target type."""
        if target.type == "local":
            return LocalDeploymentHandler(target, options)
        elif target.type == "docker":
            return DockerDeploymentHandler(target, options)
        elif target.type == "ssh":
            # For now, return a placeholder handler
            class SSHHandler(BaseDeploymentHandler):
                def deploy(self, pack_source: Path, pack_name: str) -> Dict[str, Any]:
                    return {"success": False, "error": "SSH deployment not yet implemented"}

                def status(self) -> Dict[str, Any]:
                    return {"error": "SSH status not yet implemented", "packs": []}

                def rollback(
                    self, pack_name: str, to_version: Optional[str] = None
                ) -> Dict[str, Any]:
                    return {"success": False, "error": "SSH rollback not yet implemented"}

                def uninstall(self, pack_name: str) -> Dict[str, Any]:
                    return {"success": False, "error": "SSH uninstall not yet implemented"}

            return SSHHandler(target, options)
        else:
            raise ValueError(f"Unsupported target type: {target.type}")


class PackInstaller:
    """Handles pack installation and management."""

    def __init__(self, install_dir: str = "./installed_packs"):
        self.install_dir = Path(install_dir)
        self.install_dir.mkdir(parents=True, exist_ok=True)

        # Create index file if it doesn't exist
        self.index_file = self.install_dir / ".pack_index.yaml"
        if not self.index_file.exists():
            self._create_empty_index()

    def _create_empty_index(self):
        """Create an empty pack index."""
        index = {"installed_packs": [], "version": "1.0"}
        with open(self.index_file, "w") as f:
            yaml.dump(index, f)

    def _load_index(self) -> Dict[str, Any]:
        """Load the pack index."""
        try:
            with open(self.index_file, "r") as f:
                return yaml.safe_load(f) or {"installed_packs": [], "version": "1.0"}
        except Exception:
            return {"installed_packs": [], "version": "1.0"}

    def _save_index(self, index: Dict[str, Any]):
        """Save the pack index."""
        with open(self.index_file, "w") as f:
            yaml.dump(index, f)

    def install(self, source: str) -> InstalledPack:
        """Install a pack from various sources."""
        source_path = Path(source)

        if source_path.exists():
            return self._install_from_path(source_path)
        elif self._is_url(source):
            return self._install_from_url(source)
        else:
            raise ValueError(f"Invalid source: {source}")

    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _install_from_path(self, source_path: Path) -> InstalledPack:
        """Install pack from local path."""
        if source_path.is_file() and source_path.suffix in [".yaml", ".yml"]:
            # Single pack file
            pack_data = self._load_pack_file(source_path)
            pack_name = pack_data["metadata"]["name"]

            # Create pack directory
            pack_dir = self.install_dir / pack_name
            pack_dir.mkdir(exist_ok=True)

            # Copy pack file
            shutil.copy2(source_path, pack_dir / "pack.yaml")

        elif source_path.is_dir():
            # Pack directory
            pack_file = self._find_pack_file(source_path)
            if not pack_file:
                raise ValueError(f"No pack.yaml found in {source_path}")

            pack_data = self._load_pack_file(pack_file)
            pack_name = pack_data["metadata"]["name"]

            # Create pack directory
            pack_dir = self.install_dir / pack_name
            if pack_dir.exists():
                shutil.rmtree(pack_dir)

            # Copy entire directory
            shutil.copytree(source_path, pack_dir)
        else:
            raise ValueError(f"Invalid source path: {source_path}")

        # Validate the installed pack
        validator = PackValidator()
        result = validator.validate_pack_file(str(pack_dir / "pack.yaml"))
        if not result.is_valid:
            # Clean up failed installation
            if pack_dir.exists():
                shutil.rmtree(pack_dir)
            raise ValueError(f"Pack validation failed: {result.errors}")

        # Update index
        installed_pack = InstalledPack(
            name=pack_data["metadata"]["name"],
            version=pack_data["metadata"]["version"],
            description=pack_data["metadata"].get("description", ""),
            path=str(pack_dir),
        )

        self._add_to_index(installed_pack)
        return installed_pack

    def _install_from_url(self, url: str) -> InstalledPack:
        """Install pack from URL."""
        # Download pack file
        response = requests.get(url)
        response.raise_for_status()

        # Create temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(response.text)
            temp_path = f.name

        try:
            return self._install_from_path(Path(temp_path))
        finally:
            os.unlink(temp_path)

    def _load_pack_file(self, pack_file: Path) -> Dict[str, Any]:
        """Load and parse pack file."""
        with open(pack_file, "r") as f:
            return yaml.safe_load(f)

    def _find_pack_file(self, directory: Path) -> Optional[Path]:
        """Find pack.yaml file in directory."""
        for name in ["pack.yaml", "pack.yml"]:
            pack_file = directory / name
            if pack_file.exists():
                return pack_file
        return None

    def _add_to_index(self, installed_pack: InstalledPack):
        """Add pack to installation index."""
        index = self._load_index()

        # Remove existing pack with same name
        index["installed_packs"] = [
            p for p in index["installed_packs"] if p.get("name") != installed_pack.name
        ]

        # Add new pack
        index["installed_packs"].append(
            {
                "name": installed_pack.name,
                "version": installed_pack.version,
                "description": installed_pack.description,
                "path": installed_pack.path,
                "installed_at": self._get_timestamp(),
            }
        )

        self._save_index(index)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()

    def list_installed(self) -> List[InstalledPack]:
        """List all installed packs."""
        index = self._load_index()
        packs = []

        for pack_data in index.get("installed_packs", []):
            pack = InstalledPack(
                name=pack_data["name"],
                version=pack_data["version"],
                description=pack_data.get("description", ""),
                path=pack_data["path"],
            )
            packs.append(pack)

        return packs

    def uninstall(self, pack_name: str) -> bool:
        """Uninstall a pack."""
        index = self._load_index()

        # Find pack in index
        pack_to_remove = None
        for pack_data in index.get("installed_packs", []):
            if pack_data["name"] == pack_name:
                pack_to_remove = pack_data
                break

        if not pack_to_remove:
            return False

        # Remove pack directory
        pack_path = Path(pack_to_remove["path"])
        if pack_path.exists():
            shutil.rmtree(pack_path)

        # Update index
        index["installed_packs"] = [p for p in index["installed_packs"] if p["name"] != pack_name]
        self._save_index(index)

        return True

    def get_pack_info(self, pack_name: str) -> Optional[InstalledPack]:
        """Get information about an installed pack."""
        for pack in self.list_installed():
            if pack.name == pack_name:
                return pack
        return None

    def update_pack(self, pack_name: str, source: str) -> InstalledPack:
        """Update an existing pack."""
        # Uninstall old version
        if not self.uninstall(pack_name):
            raise ValueError(f"Pack {pack_name} not found")

        # Install new version
        return self.install(source)


class PackRegistry:
    """Simple pack registry for discovering available packs."""

    def __init__(self):
        # This could be extended to support remote registries
        self.registry_url = (
            "https://raw.githubusercontent.com/catalyst-packs/registry/main/index.yaml"
        )

    def list_available(self) -> List[Dict[str, Any]]:
        """List available packs from registry."""
        try:
            response = requests.get(self.registry_url, timeout=10)
            response.raise_for_status()
            data = yaml.safe_load(response.text)
            return data.get("packs", [])
        except Exception:
            # Return empty list if registry unavailable
            return []

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for packs in registry."""
        available_packs = self.list_available()
        results = []

        query_lower = query.lower()
        for pack in available_packs:
            if (
                query_lower in pack.get("name", "").lower()
                or query_lower in pack.get("description", "").lower()
                or query_lower in " ".join(pack.get("tags", [])).lower()
            ):
                results.append(pack)

        return results
