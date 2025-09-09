"""
Unit tests for pack installer functionality.
"""

import pytest
import yaml
import json
from pathlib import Path
from catalyst_pack_schemas import (
    PackInstaller, MCPInstaller, InstalledPack, PackRegistry,
    DeploymentTarget, DeploymentOptions
)


class TestDeploymentTarget:
    """Test DeploymentTarget dataclass."""
    
    def test_deployment_target_creation(self):
        """Test creating DeploymentTarget instance."""
        target = DeploymentTarget(
            type='local',
            location='/path/to/mcp/server',
            config={'mode': 'development'}
        )
        
        assert target.type == 'local'
        assert target.location == '/path/to/mcp/server'
        assert target.config['mode'] == 'development'
    
    def test_deployment_target_without_config(self):
        """Test DeploymentTarget without config."""
        target = DeploymentTarget(type='ssh', location='server.com')
        
        assert target.type == 'ssh'
        assert target.location == 'server.com'
        assert target.config == {}


class TestDeploymentOptions:
    """Test DeploymentOptions dataclass."""
    
    def test_deployment_options_defaults(self):
        """Test DeploymentOptions with default values."""
        options = DeploymentOptions()
        
        assert options.mode == 'development'
        assert options.validate is True
        assert options.backup is True
        assert options.hot_reload is False
        assert options.dry_run is False
        assert options.force is False
        assert options.env_file is None
        assert options.secrets_source is None
    
    def test_deployment_options_custom(self):
        """Test DeploymentOptions with custom values."""
        options = DeploymentOptions(
            mode='production',
            validate=False,
            backup=False,
            hot_reload=True,
            dry_run=True,
            force=True,
            env_file='/path/to/.env',
            secrets_source='vault'
        )
        
        assert options.mode == 'production'
        assert options.validate is False
        assert options.backup is False
        assert options.hot_reload is True
        assert options.dry_run is True
        assert options.force is True
        assert options.env_file == '/path/to/.env'
        assert options.secrets_source == 'vault'


class TestInstalledPack:
    """Test InstalledPack class."""
    
    def test_installed_pack_creation(self):
        """Test creating InstalledPack instance."""
        pack = InstalledPack(
            name='test_pack',
            version='1.0.0',
            description='Test pack for installation',
            path='/path/to/installed/pack'
        )
        
        assert pack.name == 'test_pack'
        assert pack.version == '1.0.0'
        assert pack.description == 'Test pack for installation'
        assert pack.path == '/path/to/installed/pack'


class TestMCPInstaller:
    """Test MCPInstaller class."""
    
    def test_mcp_installer_initialization(self):
        """Test MCPInstaller can be initialized."""
        installer = MCPInstaller()
        
        assert hasattr(installer, 'supported_targets')
        assert 'local' in installer.supported_targets
        assert 'ssh' in installer.supported_targets
        assert 'docker' in installer.supported_targets
        assert installer.deployment_history == []
    
    def test_deploy_placeholder_functionality(self, temp_dir):
        """Test deploy method returns placeholder response."""
        installer = MCPInstaller()
        
        # Create a test pack
        pack_dir = temp_dir / 'test_pack'
        pack_dir.mkdir()
        
        target = DeploymentTarget(type='local', location=str(temp_dir))
        options = DeploymentOptions(mode='development')
        
        result = installer.deploy(pack_dir, target, options)
        
        assert result['success'] is False
        assert 'Pack validation failed' in result['error'] or 'pack.yaml not found' in result['error']
        assert 'validation_errors' in result
        assert 'pack.yaml not found' in result['validation_errors']
    
    def test_deploy_with_string_target(self, temp_dir):
        """Test deploy with string target."""
        installer = MCPInstaller()
        pack_dir = temp_dir / 'test_pack'
        pack_dir.mkdir()
        
        result = installer.deploy(pack_dir, str(temp_dir))
        
        assert result['success'] is False
        assert 'under development' in result['error']
        assert result['target'] == str(temp_dir)
    
    def test_deploy_without_options(self, temp_dir):
        """Test deploy without explicit options."""
        installer = MCPInstaller()
        pack_dir = temp_dir / 'test_pack'
        pack_dir.mkdir()
        
        result = installer.deploy(pack_dir)
        
        assert result['success'] is False
        assert 'options' in result
        assert result['options']['mode'] == 'development'  # Default
    
    def test_status_placeholder_functionality(self):
        """Test status method returns placeholder response."""
        installer = MCPInstaller()
        
        target = DeploymentTarget(type='local', location='/path/to/mcp')
        result = installer.status(target)
        
        assert 'packs' in result
        assert result['packs'] == []
        assert 'under development' in result['message']
        assert result['target'] == str(target)
    
    def test_rollback_placeholder_functionality(self):
        """Test rollback method returns placeholder response."""
        installer = MCPInstaller()
        
        target = DeploymentTarget(type='local', location='/path/to/mcp')
        result = installer.rollback('test_pack', target, '1.0.0')
        
        assert result['success'] is False
        assert 'under development' in result['error']
        assert result['pack_name'] == 'test_pack'
        assert result['target'] == str(target)
        assert result['to_version'] == '1.0.0'
    
    def test_uninstall_placeholder_functionality(self):
        """Test uninstall method returns placeholder response."""
        installer = MCPInstaller()
        
        target = DeploymentTarget(type='local', location='/path/to/mcp')
        result = installer.uninstall('test_pack', target)
        
        assert result['success'] is False
        assert 'under development' in result['error']
        assert result['pack_name'] == 'test_pack'
        assert result['target'] == str(target)


class TestPackInstaller:
    """Test PackInstaller class."""
    
    def test_pack_installer_initialization(self, temp_dir):
        """Test PackInstaller initialization."""
        install_dir = temp_dir / 'installed_packs'
        installer = PackInstaller(str(install_dir))
        
        assert installer.install_dir == install_dir
        assert install_dir.exists()
        assert installer.index_file.exists()
    
    def test_create_empty_index(self, temp_dir):
        """Test creating empty index file."""
        install_dir = temp_dir / 'test_install'
        installer = PackInstaller(str(install_dir))
        
        with open(installer.index_file) as f:
            index = yaml.safe_load(f)
        
        assert 'installed_packs' in index
        assert index['installed_packs'] == []
        assert index['version'] == '1.0'
    
    def test_load_index(self, temp_dir):
        """Test loading pack index."""
        install_dir = temp_dir / 'test_load'
        installer = PackInstaller(str(install_dir))
        
        # Add test data to index
        test_data = {
            'installed_packs': [{'name': 'test_pack', 'version': '1.0.0'}],
            'version': '1.0'
        }
        
        with open(installer.index_file, 'w') as f:
            yaml.dump(test_data, f)
        
        index = installer._load_index()
        
        assert len(index['installed_packs']) == 1
        assert index['installed_packs'][0]['name'] == 'test_pack'
    
    def test_save_index(self, temp_dir):
        """Test saving pack index."""
        install_dir = temp_dir / 'test_save'
        installer = PackInstaller(str(install_dir))
        
        test_data = {
            'installed_packs': [{'name': 'saved_pack', 'version': '2.0.0'}],
            'version': '1.0'
        }
        
        installer._save_index(test_data)
        
        with open(installer.index_file) as f:
            loaded_data = yaml.safe_load(f)
        
        assert loaded_data['installed_packs'][0]['name'] == 'saved_pack'
    
    def test_is_url(self, temp_dir):
        """Test URL detection."""
        installer = PackInstaller(str(temp_dir))
        
        assert installer._is_url('https://example.com/pack.yaml') is True
        assert installer._is_url('http://example.com/pack.yaml') is True
        assert installer._is_url('ftp://example.com/pack.yaml') is True
        assert installer._is_url('/local/path/pack.yaml') is False
        assert installer._is_url('pack.yaml') is False
        assert installer._is_url('invalid-url') is False
    
    def test_install_from_path_single_file(self, temp_dir, create_test_pack):
        """Test installing from single pack file."""
        # Create test pack and get the YAML file
        pack_dir = create_test_pack('install_test_pack')
        pack_yaml = pack_dir / 'pack.yaml'
        
        install_dir = temp_dir / 'install_test'
        installer = PackInstaller(str(install_dir))
        
        # Mock the PackValidator to avoid import issues
        from unittest.mock import patch, MagicMock
        
        with patch('catalyst_pack_schemas.installer.PackValidator') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_validator.return_value.validate_pack_file.return_value = mock_result
            
            installed_pack = installer._install_from_path(pack_yaml)
        
        assert installed_pack.name == 'install_test_pack'
        assert installed_pack.version == '1.0.0'
        
        # Check that pack was copied to install directory
        installed_pack_dir = install_dir / 'install_test_pack'
        assert installed_pack_dir.exists()
        assert (installed_pack_dir / 'pack.yaml').exists()
    
    def test_install_from_path_directory(self, temp_dir, create_test_pack):
        """Test installing from pack directory."""
        pack_dir = create_test_pack('dir_install_pack')
        
        install_dir = temp_dir / 'dir_install_test'
        installer = PackInstaller(str(install_dir))
        
        from unittest.mock import patch, MagicMock
        
        with patch('catalyst_pack_schemas.installer.PackValidator') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_validator.return_value.validate_pack_file.return_value = mock_result
            
            installed_pack = installer._install_from_path(pack_dir)
        
        assert installed_pack.name == 'dir_install_pack'
        
        # Check that entire directory was copied
        installed_pack_dir = install_dir / 'dir_install_pack'
        assert installed_pack_dir.exists()
        assert (installed_pack_dir / 'pack.yaml').exists()
        assert (installed_pack_dir / 'README.md').exists()
    
    def test_install_validation_failure(self, temp_dir, create_test_pack):
        """Test installation with validation failure."""
        pack_dir = create_test_pack('invalid_pack')
        
        install_dir = temp_dir / 'install_invalid'
        installer = PackInstaller(str(install_dir))
        
        from unittest.mock import patch, MagicMock
        
        with patch('catalyst_pack_schemas.installer.PackValidator') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = False
            mock_result.errors = ['Validation error']
            mock_validator.return_value.validate_pack_file.return_value = mock_result
            
            with pytest.raises(ValueError, match="Pack validation failed"):
                installer._install_from_path(pack_dir)
    
    def test_find_pack_file(self, temp_dir):
        """Test finding pack.yaml file in directory."""
        installer = PackInstaller(str(temp_dir))
        
        # Create directory with pack.yaml
        pack_dir = temp_dir / 'pack_with_yaml'
        pack_dir.mkdir()
        (pack_dir / 'pack.yaml').write_text('test: data')
        
        found_file = installer._find_pack_file(pack_dir)
        assert found_file == pack_dir / 'pack.yaml'
        
        # Test with pack.yml
        pack_dir2 = temp_dir / 'pack_with_yml'
        pack_dir2.mkdir()
        (pack_dir2 / 'pack.yml').write_text('test: data')
        
        found_file2 = installer._find_pack_file(pack_dir2)
        assert found_file2 == pack_dir2 / 'pack.yml'
        
        # Test with no pack file
        empty_dir = temp_dir / 'empty'
        empty_dir.mkdir()
        
        found_file3 = installer._find_pack_file(empty_dir)
        assert found_file3 is None
    
    def test_add_to_index(self, temp_dir):
        """Test adding pack to index."""
        installer = PackInstaller(str(temp_dir))
        
        pack = InstalledPack(
            name='index_test_pack',
            version='1.0.0',
            description='Test pack for index',
            path=str(temp_dir / 'index_test_pack')
        )
        
        installer._add_to_index(pack)
        
        index = installer._load_index()
        assert len(index['installed_packs']) == 1
        assert index['installed_packs'][0]['name'] == 'index_test_pack'
        assert 'installed_at' in index['installed_packs'][0]
    
    def test_list_installed(self, temp_dir):
        """Test listing installed packs."""
        installer = PackInstaller(str(temp_dir))
        
        # Add test pack to index
        test_index = {
            'installed_packs': [
                {
                    'name': 'test_pack_1',
                    'version': '1.0.0',
                    'description': 'First test pack',
                    'path': str(temp_dir / 'test_pack_1'),
                    'installed_at': '2023-01-01T00:00:00'
                },
                {
                    'name': 'test_pack_2',
                    'version': '2.0.0',
                    'description': 'Second test pack',
                    'path': str(temp_dir / 'test_pack_2'),
                    'installed_at': '2023-01-02T00:00:00'
                }
            ],
            'version': '1.0'
        }
        
        installer._save_index(test_index)
        
        packs = installer.list_installed()
        
        assert len(packs) == 2
        assert packs[0].name == 'test_pack_1'
        assert packs[1].name == 'test_pack_2'
        assert packs[1].version == '2.0.0'
    
    def test_get_pack_info(self, temp_dir):
        """Test getting pack info."""
        installer = PackInstaller(str(temp_dir))
        
        # Add test pack
        test_index = {
            'installed_packs': [
                {
                    'name': 'info_test_pack',
                    'version': '3.0.0',
                    'description': 'Pack for info test',
                    'path': str(temp_dir / 'info_test_pack'),
                    'installed_at': '2023-01-01T00:00:00'
                }
            ],
            'version': '1.0'
        }
        
        installer._save_index(test_index)
        
        pack_info = installer.get_pack_info('info_test_pack')
        assert pack_info is not None
        assert pack_info.name == 'info_test_pack'
        assert pack_info.version == '3.0.0'
        
        # Test non-existent pack
        non_existent = installer.get_pack_info('non_existent_pack')
        assert non_existent is None
    
    def test_uninstall(self, temp_dir):
        """Test uninstalling a pack."""
        installer = PackInstaller(str(temp_dir))
        
        # Create fake installed pack
        pack_dir = temp_dir / 'uninstall_test_pack'
        pack_dir.mkdir()
        (pack_dir / 'pack.yaml').write_text('test: data')
        
        test_index = {
            'installed_packs': [
                {
                    'name': 'uninstall_test_pack',
                    'version': '1.0.0',
                    'description': 'Pack to uninstall',
                    'path': str(pack_dir),
                    'installed_at': '2023-01-01T00:00:00'
                }
            ],
            'version': '1.0'
        }
        
        installer._save_index(test_index)
        
        # Uninstall the pack
        result = installer.uninstall('uninstall_test_pack')
        
        assert result is True
        assert not pack_dir.exists()  # Directory should be removed
        
        # Check index was updated
        index = installer._load_index()
        assert len(index['installed_packs']) == 0
        
        # Test uninstalling non-existent pack
        result2 = installer.uninstall('non_existent_pack')
        assert result2 is False


class TestPackRegistry:
    """Test PackRegistry class."""
    
    def test_pack_registry_initialization(self):
        """Test PackRegistry initialization."""
        registry = PackRegistry()
        
        assert hasattr(registry, 'registry_url')
        assert 'github.com' in registry.registry_url
    
    def test_list_available_no_network(self):
        """Test listing available packs without network."""
        registry = PackRegistry()
        
        # Mock requests to simulate network failure
        from unittest.mock import patch, MagicMock
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception('Network error')
            
            packs = registry.list_available()
            
            # Should return empty list on error
            assert packs == []
    
    def test_search_no_results(self):
        """Test search with no results."""
        registry = PackRegistry()
        
        from unittest.mock import patch
        
        with patch.object(registry, 'list_available', return_value=[]):
            results = registry.search('nonexistent')
            assert results == []
    
    def test_search_with_results(self):
        """Test search with mock results."""
        registry = PackRegistry()
        
        mock_packs = [
            {
                'name': 'test_pack',
                'description': 'A test pack for testing',
                'tags': ['test', 'example']
            },
            {
                'name': 'another_pack',
                'description': 'Another pack',
                'tags': ['utility']
            }
        ]
        
        from unittest.mock import patch
        
        with patch.object(registry, 'list_available', return_value=mock_packs):
            # Search by name
            results = registry.search('test')
            assert len(results) == 1
            assert results[0]['name'] == 'test_pack'
            
            # Search by description
            results2 = registry.search('Another')
            assert len(results2) == 1
            assert results2[0]['name'] == 'another_pack'
            
            # Search by tag
            results3 = registry.search('utility')
            assert len(results3) == 1
            assert results3[0]['name'] == 'another_pack'
            
            # Search with no matches
            results4 = registry.search('nomatch')
            assert len(results4) == 0