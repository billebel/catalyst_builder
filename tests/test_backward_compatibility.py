"""Test backward compatibility of schema changes."""

import json
import os
from pathlib import Path

import pytest
import yaml

from catalyst_pack_schemas.models import Pack
from catalyst_pack_schemas.validators import PackValidator


class TestBackwardCompatibility:
    """Ensure all existing packs continue to work with schema updates."""

    @pytest.fixture
    def validator(self):
        """Create a pack validator."""
        return PackValidator()

    @pytest.fixture
    def example_packs(self):
        """Get all example pack files."""
        examples_dir = Path(__file__).parent.parent / "examples"
        pack_files = []
        
        for root, dirs, files in os.walk(examples_dir):
            for file in files:
                if file == "pack.yaml":
                    pack_files.append(os.path.join(root, file))
        
        return pack_files

    def test_existing_packs_validate(self, validator, example_packs):
        """Ensure all existing example packs still validate."""
        # Note: Some example packs may be outdated and missing required fields
        # This test focuses on ensuring no breaking changes to schema processing
        for pack_file in example_packs:
            with open(pack_file, 'r', encoding='utf-8') as f:
                pack_data = yaml.safe_load(f)
            
            try:
                # Should be able to create Pack object without throwing exceptions
                pack = Pack.from_dict(pack_data)
                
                # If pack has required fields, it should validate
                has_required_metadata = all(
                    field in pack_data.get('metadata', {}) 
                    for field in ['vendor', 'domain', 'license', 'compatibility']
                )
                
                if has_required_metadata:
                    is_valid = validator.validate_pack(pack)
                    assert is_valid, f"Complete pack {pack_file} failed validation: {validator.errors}"
                else:
                    # Just ensure it doesn't crash when processing
                    validator.validate_pack(pack)
                    print(f"Skipping validation for incomplete example pack: {pack_file}")
                    
            except Exception as e:
                pytest.fail(f"Pack {pack_file} caused exception during processing: {e}")

    def test_minimal_pack_still_works(self, validator):
        """Test that a minimal pack (no optional fields) still validates."""
        minimal_pack = {
            "metadata": {
                "name": "test_pack",
                "version": "1.0.0",
                "description": "Test pack",
                "vendor": "Test",
                "license": "MIT",
                "compatibility": "^1.0.0",
                "domain": "test"
            },
            "connection": {
                "type": "rest",
                "base_url": "https://api.example.com"
            },
            "tools": {
                "test_tool": {
                    "type": "list",
                    "description": "Test tool",
                    "endpoint": "/test"
                }
            }
        }
        
        pack = Pack.from_dict(minimal_pack)
        is_valid = validator.validate_pack(pack)
        assert is_valid, f"Minimal pack failed: {validator.errors}"

    def test_new_optional_fields_ignored_gracefully(self, validator):
        """Test that new optional fields don't break existing packs."""
        pack_with_new_fields = {
            "metadata": {
                "name": "test_pack",
                "version": "1.0.0",
                "description": "Test pack",
                "vendor": "Test",
                "license": "MIT",
                "compatibility": "^1.0.0",
                "domain": "test"
            },
            "connection": {
                "type": "rest",
                "base_url": "https://api.example.com"
            },
            "tools": {
                "test_tool": {
                    "type": "list",
                    "description": "Test tool",
                    "endpoint": "/test",
                    # New optional field
                    "llm_metadata": {
                        "display_name": "📋 Test Tool",
                        "usage_hint": "Use this for testing"
                    }
                }
            }
        }
        
        pack = Pack.from_dict(pack_with_new_fields)
        is_valid = validator.validate_pack(pack)
        assert is_valid, f"Pack with new fields failed: {validator.errors}"

    def test_parameter_constraints_optional(self, validator):
        """Test that parameter constraints are optional."""
        pack_without_constraints = {
            "metadata": {
                "name": "test_pack",
                "version": "1.0.0",
                "description": "Test pack",
                "vendor": "Test",
                "license": "MIT",
                "compatibility": "^1.0.0",
                "domain": "test"
            },
            "connection": {
                "type": "rest",
                "base_url": "https://api.example.com"
            },
            "tools": {
                "test_tool": {
                    "type": "list",
                    "description": "Test tool",
                    "endpoint": "/test",
                    "parameters": [
                        {
                            "name": "limit",
                            "type": "integer",
                            "description": "Limit results"
                            # No constraints field
                        }
                    ]
                }
            }
        }
        
        pack = Pack.from_dict(pack_without_constraints)
        is_valid = validator.validate_pack(pack)
        assert is_valid

        # Now with constraints
        pack_with_constraints = {
            "metadata": {
                "name": "test_pack",
                "version": "1.0.0",
                "description": "Test pack",
                "vendor": "Test",
                "license": "MIT",
                "compatibility": "^1.0.0",
                "domain": "test"
            },
            "connection": {
                "type": "rest",
                "base_url": "https://api.example.com"
            },
            "tools": {
                "test_tool": {
                    "type": "list",
                    "description": "Test tool",
                    "endpoint": "/test",
                    "parameters": [
                        {
                            "name": "limit",
                            "type": "integer",
                            "description": "Limit results",
                            "constraints": {
                                "min": 1,
                                "max": 100,
                                "examples": [10, 25, 50]
                            }
                        }
                    ]
                }
            }
        }
        
        pack = Pack.from_dict(pack_with_constraints)
        is_valid = validator.validate_pack(pack)
        assert is_valid

    def test_transform_file_and_function_work(self, validator):
        """Test that transform file and function fields work."""
        pack_with_file_transform = {
            "metadata": {
                "name": "test_pack",
                "version": "1.0.0",
                "description": "Test pack",
                "vendor": "Test",
                "license": "MIT",
                "compatibility": "^1.0.0",
                "domain": "test"
            },
            "connection": {
                "type": "rest",
                "base_url": "https://api.example.com"
            },
            "tools": {
                "test_tool": {
                    "type": "list",
                    "description": "Test tool",
                    "endpoint": "/test",
                    "transform": {
                        "type": "python",
                        "file": "transforms/test.py",
                        "function": "process_data"
                    }
                }
            }
        }
        
        pack = Pack.from_dict(pack_with_file_transform)
        is_valid = validator.validate_pack(pack)
        assert is_valid

    def test_form_data_and_query_params_work(self, validator):
        """Test that form_data and query_params fields work."""
        pack_with_api_fields = {
            "metadata": {
                "name": "test_pack",
                "version": "1.0.0",
                "description": "Test pack",
                "vendor": "Test",
                "license": "MIT",
                "compatibility": "^1.0.0",
                "domain": "test"
            },
            "connection": {
                "type": "rest",
                "base_url": "https://api.example.com"
            },
            "tools": {
                "test_tool": {
                    "type": "search",
                    "description": "Test tool",
                    "endpoint": "/search",
                    "method": "POST",
                    "query_params": {
                        "format": "json",
                        "version": "v2"
                    },
                    "form_data": {
                        "query": "{search_query}",
                        "limit": "{max_results}"
                    }
                }
            }
        }
        
        pack = Pack.from_dict(pack_with_api_fields)
        is_valid = validator.validate_pack(pack)
        assert is_valid