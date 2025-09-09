"""
Unit tests for pack validators.
"""

import pytest
import yaml
from pathlib import Path
from catalyst_pack_schemas import PackValidator, PackCollectionValidator, validate_pack_yaml, validate_pack_dict
from catalyst_pack_schemas.models import Pack


class TestPackValidator:
    """Test PackValidator class."""
    
    def test_validator_initialization(self):
        """Test validator can be initialized."""
        validator = PackValidator()
        assert validator.errors == []
        assert validator.warnings == []
    
    def test_validate_valid_pack(self, sample_pack_data):
        """Test validation of a valid pack."""
        pack = Pack.from_dict(sample_pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is True
        assert len(validator.errors) == 0
    
    def test_validate_pack_missing_metadata_fields(self, sample_pack_data):
        """Test validation with missing metadata fields."""
        pack_data = sample_pack_data.copy()
        del pack_data['metadata']['name']
        del pack_data['metadata']['vendor']
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert 'metadata.name is required' in validator.errors
        assert 'metadata.vendor is required' in validator.errors
    
    def test_validate_pack_invalid_pricing_tier(self, sample_pack_data):
        """Test validation with invalid pricing tier."""
        pack_data = sample_pack_data.copy()
        pack_data['metadata']['pricing_tier'] = 'invalid_tier'
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert any('Invalid pricing_tier' in error for error in validator.errors)
    
    def test_validate_pack_invalid_connection_type(self, sample_pack_data):
        """Test validation with invalid connection type."""
        pack_data = sample_pack_data.copy()
        pack_data['connection']['type'] = 'invalid_type'
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert any('Invalid connection.type' in error for error in validator.errors)
    
    def test_validate_rest_connection_missing_base_url(self, sample_pack_data):
        """Test validation of REST connection missing base_url."""
        pack_data = sample_pack_data.copy()
        del pack_data['connection']['base_url']
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert 'connection.base_url is required for REST connections' in validator.errors
    
    def test_validate_database_connection_requirements(self, sample_pack_data):
        """Test validation of database connection requirements."""
        pack_data = sample_pack_data.copy()
        pack_data['connection'] = {
            'type': 'database',
            'timeout': 30
        }
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert 'connection.engine is required for database connections' in validator.errors
        assert 'connection.host is required for database connections' in validator.errors
    
    def test_validate_ssh_connection_requirements(self, sample_pack_data):
        """Test validation of SSH connection requirements."""
        pack_data = sample_pack_data.copy()
        pack_data['connection'] = {
            'type': 'ssh',
            'timeout': 30
        }
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert 'connection.hostname is required for SSH connections' in validator.errors
        assert 'connection.username is required for SSH connections' in validator.errors
    
    def test_validate_negative_timeout(self, sample_pack_data):
        """Test validation with negative timeout."""
        pack_data = sample_pack_data.copy()
        pack_data['connection']['timeout'] = -5
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert 'connection.timeout must be positive' in validator.errors
    
    def test_validate_tool_missing_description(self, sample_pack_data):
        """Test validation of tool missing description."""
        pack_data = sample_pack_data.copy()
        del pack_data['tools']['test_tool']['description']
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert 'Tool test_tool: description is required' in validator.errors
    
    def test_validate_tool_missing_type(self, sample_pack_data):
        """Test validation of tool missing type - now provides default, so should pass."""
        pack_data = sample_pack_data.copy()
        del pack_data['tools']['test_tool']['type']
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        # With default type provided, validation should now pass
        assert result is True
    
    def test_validate_modular_pack_with_structure(self, sample_modular_pack_data):
        """Test validation of modular pack with structure section."""
        pack = Pack.from_dict(sample_modular_pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        # Should pass even without inline tools due to structure section
        assert result is True
    
    def test_validate_prompt_missing_template(self, sample_pack_data):
        """Test validation of prompt missing template."""
        pack_data = sample_pack_data.copy()
        del pack_data['prompts']['test_prompt']['template']
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert 'Prompt test_prompt: template is required' in validator.errors
    
    def test_validate_resource_missing_url(self, sample_pack_data):
        """Test validation of resource missing URL."""
        pack_data = sample_pack_data.copy()
        del pack_data['resources']['test_docs']['url']
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is False
        assert 'Resource test_docs: url is required' in validator.errors
    
    def test_get_validation_report(self, sample_pack_data):
        """Test getting validation report."""
        pack_data = sample_pack_data.copy()
        del pack_data['metadata']['name']  # Create an error
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        validator.validate_pack(pack)
        
        report = validator.get_validation_report()
        
        assert 'valid' in report
        assert 'errors' in report
        assert 'warnings' in report
        assert 'error_count' in report
        assert 'warning_count' in report
        assert report['valid'] is False
        assert report['error_count'] > 0


class TestValidationFunctions:
    """Test standalone validation functions."""
    
    def test_validate_pack_yaml_file(self, create_test_pack):
        """Test validating pack from YAML file."""
        pack_dir = create_test_pack('yaml_validation_test')
        pack_yaml = pack_dir / 'pack.yaml'
        
        result = validate_pack_yaml(str(pack_yaml))
        
        assert result['valid'] is True
        assert result['error_count'] == 0
    
    def test_validate_pack_yaml_file_not_found(self):
        """Test validating non-existent YAML file."""
        result = validate_pack_yaml('/nonexistent/pack.yaml')
        
        assert result['valid'] is False
        assert result['error_count'] > 0
        assert 'Failed to load pack' in result['errors'][0]
    
    def test_validate_pack_dict_valid(self, sample_pack_data):
        """Test validating pack from dictionary."""
        result = validate_pack_dict(sample_pack_data)
        
        assert result['valid'] is True
        assert result['error_count'] == 0
    
    def test_validate_pack_dict_invalid(self, sample_pack_data):
        """Test validating invalid pack from dictionary."""
        pack_data = sample_pack_data.copy()
        del pack_data['metadata']['name']
        
        result = validate_pack_dict(pack_data)
        
        assert result['valid'] is False
        assert result['error_count'] > 0
    
    def test_validate_pack_dict_malformed(self):
        """Test validating malformed pack dictionary."""
        malformed_data = {'invalid': 'structure'}
        
        result = validate_pack_dict(malformed_data)
        
        assert result['valid'] is False
        assert result['error_count'] > 0
        assert 'Failed to parse pack' in result['errors'][0]


class TestPackCollectionValidator:
    """Test PackCollectionValidator class."""
    
    def test_collection_validator_initialization(self, temp_dir):
        """Test collection validator can be initialized."""
        validator = PackCollectionValidator(str(temp_dir))
        assert str(validator.base_dir) == str(temp_dir)
    
    def test_validate_all_packs(self, create_pack_collection):
        """Test validating all packs in a collection."""
        collection_dir = create_pack_collection()
        validator = PackCollectionValidator(str(collection_dir))
        
        results = validator.validate_all_packs()
        
        assert isinstance(results, dict)
        assert len(results) >= 2  # Should find valid_pack and invalid_pack
        
        # Check that valid pack is valid
        if 'valid_pack' in results:
            assert results['valid_pack']['valid'] is True
        
        # Check that invalid pack is invalid
        if 'invalid_pack' in results:
            assert results['invalid_pack']['valid'] is False
    
    def test_get_validation_summary(self, create_pack_collection):
        """Test getting validation summary."""
        collection_dir = create_pack_collection()
        validator = PackCollectionValidator(str(collection_dir))
        
        summary = validator.get_validation_summary()
        
        assert 'total_packs' in summary
        assert 'valid_packs' in summary
        assert 'invalid_packs' in summary
        assert 'total_errors' in summary
        assert 'total_warnings' in summary
        assert 'validation_rate' in summary
        assert summary['total_packs'] > 0
    
    def test_validate_empty_collection(self, temp_dir):
        """Test validating empty collection."""
        validator = PackCollectionValidator(str(temp_dir))
        
        results = validator.validate_all_packs()
        summary = validator.get_validation_summary()
        
        assert len(results) == 0
        assert summary['total_packs'] == 0
    
    def test_validate_collection_with_missing_pack_yaml(self, temp_dir):
        """Test validating collection with directory missing pack.yaml."""
        # Create directory without pack.yaml
        missing_pack_dir = temp_dir / 'missing_pack'
        missing_pack_dir.mkdir()
        
        validator = PackCollectionValidator(str(temp_dir))
        results = validator.validate_all_packs()
        
        if 'missing_pack' in results:
            assert results['missing_pack']['valid'] is False
            assert 'pack.yaml file not found' in results['missing_pack']['errors']


class TestValidationErrorHandling:
    """Test error handling in validation."""
    
    def test_validate_pack_with_yaml_syntax_error(self, temp_dir):
        """Test validation with YAML syntax error."""
        # Create pack with invalid YAML
        pack_dir = temp_dir / 'yaml_error_pack'
        pack_dir.mkdir()
        
        invalid_yaml = """
metadata:
  name: test_pack
  version: 1.0.0
  description: Test pack
  vendor: Test
  domain: test
connection:
  type: rest
  base_url: https://api.test.com
tools:
  invalid: yaml: syntax: [unclosed bracket
"""
        
        with open(pack_dir / 'pack.yaml', 'w') as f:
            f.write(invalid_yaml)
        
        result = validate_pack_yaml(str(pack_dir / 'pack.yaml'))
        
        assert result['valid'] is False
        assert result['error_count'] > 0
        # Should handle YAML parsing error gracefully
    
    def test_validate_pack_with_empty_file(self, temp_dir):
        """Test validation with empty pack file."""
        pack_dir = temp_dir / 'empty_pack'
        pack_dir.mkdir()
        
        # Create empty pack.yaml
        (pack_dir / 'pack.yaml').write_text('')
        
        result = validate_pack_yaml(str(pack_dir / 'pack.yaml'))
        
        assert result['valid'] is False
        assert result['error_count'] > 0


class TestVersionValidation:
    """Test version format validation."""
    
    def test_valid_semantic_version(self, sample_pack_data):
        """Test validation with valid semantic version."""
        pack_data = sample_pack_data.copy()
        pack_data['metadata']['version'] = '1.2.3'
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        assert result is True
        # Should not have version warning for properly formatted version
        version_warnings = [w for w in validator.warnings if 'semantic versioning' in w]
        assert len(version_warnings) == 0
    
    def test_invalid_version_format(self, sample_pack_data):
        """Test validation with invalid version format."""
        pack_data = sample_pack_data.copy()
        pack_data['metadata']['version'] = '1.0'  # Not semantic versioning
        
        pack = Pack.from_dict(pack_data)
        validator = PackValidator()
        
        result = validator.validate_pack(pack)
        # Should still be valid (warning, not error)
        assert result is True
        
        # Should have version warning
        version_warnings = [w for w in validator.warnings if 'semantic versioning' in w]
        assert len(version_warnings) == 1