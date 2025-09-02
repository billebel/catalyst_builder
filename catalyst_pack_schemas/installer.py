"""Pack installation and management utilities."""

import os
import shutil
import yaml
import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urlparse
from dataclasses import dataclass, asdict
import requests

from .models import PackMetadata
from .validators import PackValidator


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


class InstalledPack:
    """Represents an installed pack."""
    
    def __init__(self, name: str, version: str, description: str, path: str):
        self.name = name
        self.version = version
        self.description = description
        self.path = path


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
        with open(self.index_file, 'w') as f:
            yaml.dump(index, f)
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the pack index."""
        try:
            with open(self.index_file, 'r') as f:
                return yaml.safe_load(f) or {"installed_packs": [], "version": "1.0"}
        except Exception:
            return {"installed_packs": [], "version": "1.0"}
    
    def _save_index(self, index: Dict[str, Any]):
        """Save the pack index."""
        with open(self.index_file, 'w') as f:
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
        if source_path.is_file() and source_path.suffix in ['.yaml', '.yml']:
            # Single pack file
            pack_data = self._load_pack_file(source_path)
            pack_name = pack_data['metadata']['name']
            
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
            pack_name = pack_data['metadata']['name']
            
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
            name=pack_data['metadata']['name'],
            version=pack_data['metadata']['version'],
            description=pack_data['metadata'].get('description', ''),
            path=str(pack_dir)
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(response.text)
            temp_path = f.name
        
        try:
            return self._install_from_path(Path(temp_path))
        finally:
            os.unlink(temp_path)
    
    def _load_pack_file(self, pack_file: Path) -> Dict[str, Any]:
        """Load and parse pack file."""
        with open(pack_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _find_pack_file(self, directory: Path) -> Optional[Path]:
        """Find pack.yaml file in directory."""
        for name in ['pack.yaml', 'pack.yml']:
            pack_file = directory / name
            if pack_file.exists():
                return pack_file
        return None
    
    def _add_to_index(self, installed_pack: InstalledPack):
        """Add pack to installation index."""
        index = self._load_index()
        
        # Remove existing pack with same name
        index['installed_packs'] = [
            p for p in index['installed_packs'] 
            if p.get('name') != installed_pack.name
        ]
        
        # Add new pack
        index['installed_packs'].append({
            'name': installed_pack.name,
            'version': installed_pack.version,
            'description': installed_pack.description,
            'path': installed_pack.path,
            'installed_at': self._get_timestamp()
        })
        
        self._save_index(index)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def list_installed(self) -> List[InstalledPack]:
        """List all installed packs."""
        index = self._load_index()
        packs = []
        
        for pack_data in index.get('installed_packs', []):
            pack = InstalledPack(
                name=pack_data['name'],
                version=pack_data['version'],
                description=pack_data.get('description', ''),
                path=pack_data['path']
            )
            packs.append(pack)
        
        return packs
    
    def uninstall(self, pack_name: str) -> bool:
        """Uninstall a pack."""
        index = self._load_index()
        
        # Find pack in index
        pack_to_remove = None
        for pack_data in index.get('installed_packs', []):
            if pack_data['name'] == pack_name:
                pack_to_remove = pack_data
                break
        
        if not pack_to_remove:
            return False
        
        # Remove pack directory
        pack_path = Path(pack_to_remove['path'])
        if pack_path.exists():
            shutil.rmtree(pack_path)
        
        # Update index
        index['installed_packs'] = [
            p for p in index['installed_packs'] 
            if p['name'] != pack_name
        ]
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
        self.registry_url = "https://raw.githubusercontent.com/catalyst-packs/registry/main/index.yaml"
    
    def list_available(self) -> List[Dict[str, Any]]:
        """List available packs from registry."""
        try:
            response = requests.get(self.registry_url, timeout=10)
            response.raise_for_status()
            data = yaml.safe_load(response.text)
            return data.get('packs', [])
        except Exception:
            # Return empty list if registry unavailable
            return []
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for packs in registry."""
        available_packs = self.list_available()
        results = []
        
        query_lower = query.lower()
        for pack in available_packs:
            if (query_lower in pack.get('name', '').lower() or 
                query_lower in pack.get('description', '').lower() or
                query_lower in ' '.join(pack.get('tags', [])).lower()):
                results.append(pack)
        
        return results