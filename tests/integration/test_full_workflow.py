"""
Integration tests for full pack development workflow.
"""

import pytest
import yaml
import json
from pathlib import Path
from catalyst_pack_schemas import (
    create_pack, validate_pack_yaml, PackCollectionValidator,
    PackInstaller, PackValidator
)


class TestFullWorkflow:
    """Test complete pack development workflow."""
    
    def test_create_validate_install_workflow(self, temp_dir):
        """Test creating, validating, and installing a pack."""
        # Step 1: Create pack
        pack_path = create_pack(
            pack_name='workflow_test_pack',
            output_dir=str(temp_dir),
            connection_type='rest',
            base_url='https://api.workflow.com',
            domain='workflow',
            vendor='Workflow Co',
            description='Test pack for workflow integration'
        )
        
        assert pack_path.exists()
        assert (pack_path / 'pack.yaml').exists()
        
        # Step 2: Validate pack
        pack_yaml = pack_path / 'pack.yaml'
        validation_result = validate_pack_yaml(str(pack_yaml))
        
        assert validation_result['valid'] is True
        assert validation_result['error_count'] == 0
        
        # Step 3: Install pack
        install_dir = temp_dir / 'installations'
        installer = PackInstaller(str(install_dir))
        
        # Mock validation to avoid circular import issues
        from unittest.mock import patch, MagicMock
        
        with patch('catalyst_pack_schemas.installer.PackValidator') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_validator.return_value.validate_pack_file.return_value = mock_result
            
            installed_pack = installer.install(str(pack_path))
        
        assert installed_pack.name == 'workflow_test_pack'
        assert installed_pack.version == '1.0.0'
        
        # Step 4: Verify installation
        installed_packs = installer.list_installed()
        assert len(installed_packs) == 1
        assert installed_packs[0].name == 'workflow_test_pack'
        
        # Step 5: Get pack info
        pack_info = installer.get_pack_info('workflow_test_pack')
        assert pack_info is not None
        assert pack_info.description == 'Test pack for workflow integration'
    
    def test_collection_validation_workflow(self, temp_dir):
        """Test validating a collection of packs."""
        # Create multiple packs
        valid_pack = create_pack(
            pack_name='valid_pack',
            output_dir=str(temp_dir),
            connection_type='rest',
            base_url='https://api.valid.com',
            domain='valid',
            vendor='Valid Co'
        )
        
        invalid_pack_dir = temp_dir / 'invalid_pack'
        invalid_pack_dir.mkdir()
        
        # Create invalid pack (missing required fields)
        invalid_data = {
            'metadata': {
                'name': 'invalid_pack',
                'version': '1.0.0'
                # Missing required fields
            },
            'connection': {
                'type': 'rest'
                # Missing base_url
            }
        }
        
        with open(invalid_pack_dir / 'pack.yaml', 'w') as f:
            yaml.dump(invalid_data, f)
        
        # Validate collection
        validator = PackCollectionValidator(str(temp_dir))
        results = validator.validate_all_packs()
        
        assert len(results) >= 2
        assert results['valid_pack']['valid'] is True
        assert results['invalid_pack']['valid'] is False
        
        # Get summary
        summary = validator.get_validation_summary()
        assert summary['total_packs'] >= 2
        assert summary['valid_packs'] >= 1
        assert summary['invalid_packs'] >= 1
    
    def test_modular_pack_workflow(self, temp_dir):
        """Test workflow with modular pack structure."""
        # Create base pack directory
        pack_dir = temp_dir / 'modular_pack'
        pack_dir.mkdir()
        
        # Create modular structure
        tools_dir = pack_dir / 'tools'
        tools_dir.mkdir()
        
        prompts_dir = pack_dir / 'prompts'
        prompts_dir.mkdir()
        
        # Create main pack.yaml with structure
        pack_data = {
            'metadata': {
                'name': 'modular_pack',
                'version': '1.0.0',
                'description': 'Modular pack for testing',
                'vendor': 'Modular Co',
                'license': 'MIT',
                'compatibility': '2.0.0',
                'domain': 'modular',
                'pricing_tier': 'free'
            },
            'connection': {
                'type': 'rest',
                'base_url': 'https://api.modular.com',
                'timeout': 30
            },
            'structure': {
                'tools': ['tools/api-tools.yaml'],
                'prompts': ['prompts/analysis.yaml']
            }
        }
        
        with open(pack_dir / 'pack.yaml', 'w') as f:
            yaml.dump(pack_data, f)
        
        # Create tools file
        tools_data = {
            'tools': {
                'list_items': {
                    'type': 'list',
                    'description': 'List all items',
                    'endpoint': '/api/items',
                    'method': 'GET'
                },
                'search_items': {
                    'type': 'search',
                    'description': 'Search for items',
                    'endpoint': '/api/search',
                    'method': 'POST'
                }
            }
        }
        
        with open(tools_dir / 'api-tools.yaml', 'w') as f:
            yaml.dump(tools_data, f)
        
        # Create prompts file
        prompts_data = {
            'prompts': {
                'analyze_data': {
                    'name': 'Data Analysis',
                    'description': 'Analyze the provided data',
                    'template': 'Analyze this data: {data}'
                }
            }
        }
        
        with open(prompts_dir / 'analysis.yaml', 'w') as f:
            yaml.dump(prompts_data, f)
        
        # Validate modular pack
        validation_result = validate_pack_yaml(str(pack_dir / 'pack.yaml'))
        assert validation_result['valid'] is True
        
        # Test with collection validator (should handle modular structure)
        validator = PackCollectionValidator(str(temp_dir))
        results = validator.validate_all_packs()
        
        assert 'modular_pack' in results
        assert results['modular_pack']['valid'] is True
    
    def test_pack_update_workflow(self, temp_dir):
        """Test updating an installed pack."""
        # Create and install initial version
        pack_path = create_pack(
            pack_name='update_test_pack',
            output_dir=str(temp_dir),
            connection_type='rest',
            base_url='https://api.update.com',
            domain='update',
            vendor='Update Co',
            description='Pack for update testing'
        )
        
        install_dir = temp_dir / 'updates'
        installer = PackInstaller(str(install_dir))
        
        from unittest.mock import patch, MagicMock
        
        with patch('catalyst_pack_schemas.installer.PackValidator') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_validator.return_value.validate_pack_file.return_value = mock_result
            
            # Install initial version
            installed_pack = installer.install(str(pack_path))
            assert installed_pack.version == '1.0.0'
            
            # Update pack.yaml to new version
            with open(pack_path / 'pack.yaml') as f:
                pack_data = yaml.safe_load(f)
            
            pack_data['metadata']['version'] = '2.0.0'
            pack_data['metadata']['description'] = 'Updated pack for testing'
            
            with open(pack_path / 'pack.yaml', 'w') as f:
                yaml.dump(pack_data, f)
            
            # Update installed pack
            updated_pack = installer.update_pack('update_test_pack', str(pack_path))
            
            assert updated_pack.version == '2.0.0'
            assert 'Updated pack' in updated_pack.description
            
            # Verify only one version is installed
            installed_packs = installer.list_installed()
            assert len(installed_packs) == 1
            assert installed_packs[0].version == '2.0.0'
    
    def test_uninstall_workflow(self, temp_dir):
        """Test complete uninstall workflow."""
        # Create and install pack
        pack_path = create_pack(
            pack_name='uninstall_workflow_pack',
            output_dir=str(temp_dir),
            connection_type='rest',
            base_url='https://api.uninstall.com',
            domain='uninstall',
            vendor='Uninstall Co'
        )
        
        install_dir = temp_dir / 'uninstall_test'
        installer = PackInstaller(str(install_dir))
        
        from unittest.mock import patch, MagicMock
        
        with patch('catalyst_pack_schemas.installer.PackValidator') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_validator.return_value.validate_pack_file.return_value = mock_result
            
            # Install pack
            installed_pack = installer.install(str(pack_path))
            assert installed_pack.name == 'uninstall_workflow_pack'
            
            # Verify installation
            installed_packs = installer.list_installed()
            assert len(installed_packs) == 1
            
            # Verify pack directory exists
            pack_install_dir = Path(installed_pack.path)
            assert pack_install_dir.exists()
            
            # Uninstall pack
            result = installer.uninstall('uninstall_workflow_pack')
            assert result is True
            
            # Verify uninstallation
            installed_packs_after = installer.list_installed()
            assert len(installed_packs_after) == 0
            
            # Verify pack directory is removed
            assert not pack_install_dir.exists()
            
            # Verify pack info is gone
            pack_info = installer.get_pack_info('uninstall_workflow_pack')
            assert pack_info is None
    
    def test_error_recovery_workflow(self, temp_dir):
        """Test error recovery in workflow."""
        # Create pack with validation errors
        invalid_pack_dir = temp_dir / 'error_recovery_pack'
        invalid_pack_dir.mkdir()
        
        invalid_data = {
            'metadata': {
                'name': 'error_recovery_pack',
                'version': '1.0.0',
                'description': 'Pack with errors',
                'vendor': 'Error Co',
                'license': 'MIT',
                'compatibility': '2.0.0',
                'domain': 'errors',
                'pricing_tier': 'free'
            },
            'connection': {
                'type': 'rest'
                # Missing base_url - validation error
            },
            'tools': {
                'broken_tool': {
                    'type': 'list',
                    'description': 'Broken tool'
                    # Missing endpoint - validation error
                }
            }
        }
        
        with open(invalid_pack_dir / 'pack.yaml', 'w') as f:
            yaml.dump(invalid_data, f)
        
        # Attempt validation - should fail
        validation_result = validate_pack_yaml(str(invalid_pack_dir / 'pack.yaml'))
        assert validation_result['valid'] is False
        assert validation_result['error_count'] > 0
        
        # Fix the errors
        fixed_data = invalid_data.copy()
        fixed_data['connection']['base_url'] = 'https://api.fixed.com'
        fixed_data['tools']['broken_tool']['endpoint'] = '/api/items'
        
        with open(invalid_pack_dir / 'pack.yaml', 'w') as f:
            yaml.dump(fixed_data, f)
        
        # Re-validate - should pass
        validation_result_fixed = validate_pack_yaml(str(invalid_pack_dir / 'pack.yaml'))
        assert validation_result_fixed['valid'] is True
        assert validation_result_fixed['error_count'] == 0
        
        # Now should be installable
        installer = PackInstaller(str(temp_dir / 'error_recovery'))
        
        from unittest.mock import patch, MagicMock
        
        with patch('catalyst_pack_schemas.installer.PackValidator') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_validator.return_value.validate_pack_file.return_value = mock_result
            
            installed_pack = installer.install(str(invalid_pack_dir))
            assert installed_pack.name == 'error_recovery_pack'
    
    def test_multiple_connection_types_workflow(self, temp_dir):
        """Test workflow with different connection types."""
        connection_types = [
            {
                'type': 'rest',
                'base_url': 'https://api.rest.com',
                'expected_valid': True
            },
            {
                'type': 'database',
                'engine': 'postgresql',
                'host': 'db.test.com',
                'expected_valid': True
            },
            {
                'type': 'ssh',
                'hostname': 'server.test.com',
                'username': 'testuser',
                'expected_valid': True
            }
        ]
        
        for i, conn_config in enumerate(connection_types):
            pack_name = f'conn_test_pack_{i}'
            
            # Create pack with specific connection type
            if conn_config['type'] == 'rest':
                pack_path = create_pack(
                    pack_name=pack_name,
                    output_dir=str(temp_dir),
                    connection_type='rest',
                    base_url=conn_config['base_url'],
                    domain='api',
                    vendor='API Co'
                )
            else:
                # For non-REST types, create manually since create_pack might not support all
                pack_dir = temp_dir / pack_name
                pack_dir.mkdir()
                
                pack_data = {
                    'metadata': {
                        'name': pack_name,
                        'version': '1.0.0',
                        'description': f'Pack with {conn_config["type"]} connection',
                        'vendor': 'Test Co',
                        'license': 'MIT',
                        'compatibility': '2.0.0',
                        'domain': 'testing',
                        'pricing_tier': 'free'
                    },
                    'connection': {**conn_config, 'timeout': 30},
                    'tools': {},
                    'prompts': {},
                    'resources': {}
                }
                del pack_data['connection']['expected_valid']
                
                with open(pack_dir / 'pack.yaml', 'w') as f:
                    yaml.dump(pack_data, f)
                
                pack_path = pack_dir
            
            # Validate pack
            validation_result = validate_pack_yaml(str(pack_path / 'pack.yaml'))
            
            if conn_config['expected_valid']:
                assert validation_result['valid'] is True, f"Pack {pack_name} should be valid"
            else:
                assert validation_result['valid'] is False, f"Pack {pack_name} should be invalid"