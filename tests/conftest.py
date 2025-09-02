"""
Pytest configuration and shared fixtures for catalyst_pack_schemas tests.
"""

import pytest
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

# Test fixtures and utilities


@pytest.fixture
def temp_dir():
    """Create temporary directory that's cleaned up after test."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_pack_data() -> Dict[str, Any]:
    """Sample pack YAML data for testing."""
    return {
        'metadata': {
            'name': 'test_pack',
            'version': '1.0.0',
            'description': 'Test pack for unit testing',
            'vendor': 'Test Vendor',
            'domain': 'testing',
            'compatibility': '2.0.0',
            'license': 'MIT',
            'tags': ['test', 'example'],
            'pricing_tier': 'free'
        },
        'connection': {
            'type': 'rest',
            'base_url': '${API_BASE_URL}',
            'timeout': 30,
            'auth': {
                'method': 'bearer',
                'token': '${API_TOKEN}'
            }
        },
        'tools': {
            'test_tool': {
                'type': 'list',
                'description': 'Test tool for validation',
                'endpoint': '/api/test',
                'method': 'GET',
                'parameters': [
                    {
                        'name': 'limit',
                        'type': 'integer',
                        'required': False,
                        'default': 10
                    }
                ]
            }
        },
        'prompts': {
            'test_prompt': {
                'name': 'Test Prompt',
                'description': 'Test prompt template',
                'template': 'You are a test assistant. Help with: {query}'
            }
        },
        'resources': {
            'test_docs': {
                'name': 'Test Documentation',
                'description': 'Test API documentation',
                'type': 'documentation',
                'url': 'https://docs.test.com'
            }
        }
    }


@pytest.fixture
def sample_modular_pack_data() -> Dict[str, Any]:
    """Sample modular pack YAML data for testing."""
    return {
        'metadata': {
            'name': 'modular_test_pack',
            'version': '1.0.0',
            'description': 'Modular test pack',
            'vendor': 'Test Vendor',
            'domain': 'testing',
            'compatibility': '2.0.0',
            'pricing_tier': 'free'
        },
        'connection': {
            'type': 'rest',
            'base_url': '${API_BASE_URL}',
            'timeout': 30
        },
        'structure': {
            'tools': [
                'tools/api-tools.yaml',
                'tools/admin-tools.yaml'
            ],
            'prompts': [
                'prompts/analysis-prompts.yaml'
            ]
        }
    }


@pytest.fixture
def sample_tool_file() -> Dict[str, Any]:
    """Sample tool file content for modular packs."""
    return {
        'tools': {
            'api_list': {
                'type': 'list',
                'description': 'List items from API',
                'endpoint': '/api/items',
                'method': 'GET'
            },
            'api_search': {
                'type': 'search',
                'description': 'Search API items',
                'endpoint': '/api/search',
                'method': 'POST',
                'parameters': [
                    {
                        'name': 'query',
                        'type': 'string',
                        'required': True
                    }
                ]
            }
        }
    }


@pytest.fixture
def create_test_pack(temp_dir, sample_pack_data):
    """Create a complete test pack directory structure."""
    def _create_pack(pack_name: str = 'test_pack', 
                     pack_data: Dict[str, Any] = None,
                     modular: bool = False) -> Path:
        if pack_data is None:
            pack_data = sample_pack_data.copy()
        else:
            pack_data = pack_data.copy()
            
        # Update pack name in metadata
        if 'metadata' in pack_data:
            pack_data['metadata'] = pack_data['metadata'].copy()
            pack_data['metadata']['name'] = pack_name
            
        pack_dir = temp_dir / pack_name
        pack_dir.mkdir(parents=True)
        
        # Create pack.yaml
        with open(pack_dir / 'pack.yaml', 'w') as f:
            yaml.dump(pack_data, f, default_flow_style=False)
        
        if modular:
            # Create modular structure
            tools_dir = pack_dir / 'tools'
            tools_dir.mkdir()
            
            # Create tool files
            tool_file_data = {
                'tools': {
                    'modular_tool': {
                        'type': 'list',
                        'description': 'Modular test tool',
                        'endpoint': '/api/modular',
                        'method': 'GET'
                    }
                }
            }
            
            with open(tools_dir / 'test-tools.yaml', 'w') as f:
                yaml.dump(tool_file_data, f)
            
            # Update pack.yaml for modular structure
            pack_data['structure'] = {'tools': ['tools/test-tools.yaml']}
            pack_data.pop('tools', None)  # Remove inline tools
            
            with open(pack_dir / 'pack.yaml', 'w') as f:
                yaml.dump(pack_data, f, default_flow_style=False)
        
        # Create additional files
        (pack_dir / 'README.md').write_text('# Test Pack\nTest pack for unit testing.')
        
        # Create .env file
        env_content = """API_BASE_URL=https://api.test.com
API_TOKEN=test_token_123
"""
        (pack_dir / '.env').write_text(env_content)
        
        return pack_dir
    
    return _create_pack


@pytest.fixture
def create_pack_collection(temp_dir):
    """Create a collection of test packs for testing discovery and validation."""
    def _create_collection():
        # Production packs
        production_dir = temp_dir / 'production'
        production_dir.mkdir()
        
        # Valid production pack
        valid_pack = production_dir / 'valid_pack'
        valid_pack.mkdir()
        
        valid_data = {
            'metadata': {
                'name': 'valid_pack',
                'version': '1.0.0',
                'description': 'Valid test pack',
                'vendor': 'Test Co',
                'domain': 'analytics',
                'pricing_tier': 'free'
            },
            'connection': {'type': 'rest', 'base_url': 'https://api.test.com', 'timeout': 30},
            'tools': {
                'test_tool': {
                    'type': 'list',
                    'description': 'Test tool',
                    'endpoint': '/test',
                    'method': 'GET'
                }
            }
        }
        
        with open(valid_pack / 'pack.yaml', 'w') as f:
            yaml.dump(valid_data, f)
        
        # Invalid production pack (missing required fields)
        invalid_pack = production_dir / 'invalid_pack'
        invalid_pack.mkdir()
        
        invalid_data = {
            'metadata': {
                'name': 'invalid_pack',
                'version': '1.0.0'
                # Missing required fields
            },
            'connection': {'type': 'rest'},  # Missing base_url
            'tools': {}  # No tools defined
        }
        
        with open(invalid_pack / 'pack.yaml', 'w') as f:
            yaml.dump(invalid_data, f)
        
        # Example packs
        examples_dir = temp_dir / 'examples'
        examples_dir.mkdir()
        
        example_pack = examples_dir / 'example_pack.example'
        example_pack.mkdir()
        
        with open(example_pack / 'pack.yaml', 'w') as f:
            yaml.dump(valid_data, f)
        
        return temp_dir
    
    return _create_collection


@pytest.fixture
def environment_vars():
    """Set up test environment variables."""
    import os
    
    test_env = {
        'API_BASE_URL': 'https://test-api.example.com',
        'API_TOKEN': 'test_token_12345',
        'DB_HOST': 'test-db.example.com',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password'
    }
    
    # Store original values
    original_env = {}
    for key in test_env:
        original_env[key] = os.environ.get(key)
    
    # Set test values
    for key, value in test_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]
    
    yield test_env
    
    # Restore original values
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


# Test utilities

def assert_valid_pack_yaml(pack_path: Path):
    """Assert that a pack.yaml file is valid."""
    assert pack_path.exists(), f"pack.yaml not found at {pack_path}"
    
    with open(pack_path) as f:
        pack_data = yaml.safe_load(f)
    
    # Check required sections
    assert 'metadata' in pack_data, "Missing metadata section"
    assert 'connection' in pack_data, "Missing connection section"
    
    # Check required metadata fields
    metadata = pack_data['metadata']
    required_fields = ['name', 'version', 'description', 'vendor', 'domain']
    for field in required_fields:
        assert field in metadata, f"Missing required metadata field: {field}"
    
    return pack_data


def create_malicious_pack_data():
    """Create pack data with potential security issues for testing."""
    return {
        'metadata': {
            'name': '../../../malicious_pack',  # Path traversal attempt
            'version': '1.0.0',
            'description': 'Pack with security issues',
            'vendor': 'Malicious Co',
            'domain': 'security_test',
            'pricing_tier': 'free'
        },
        'connection': {
            'type': 'rest',
            'base_url': 'http://malicious.com/api'  # Potentially dangerous URL
        },
        'tools': {
            'dangerous_tool': {
                'type': 'command',
                'description': 'Tool that might execute dangerous commands',
                'command': 'rm -rf /',  # Dangerous command
                'parameters': []
            }
        }
    }