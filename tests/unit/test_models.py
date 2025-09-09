"""
Unit tests for pack models.
"""

import pytest
import yaml
from pathlib import Path
from catalyst_pack_schemas import (
    Pack, PackMetadata, ConnectionConfig, ToolDefinition, 
    PromptDefinition, ResourceDefinition, AuthConfig,
    ToolType, AuthMethod, PackValidationError
)


class TestPackMetadata:
    """Test PackMetadata model."""
    
    def test_pack_metadata_creation(self):
        """Test creating PackMetadata instance."""
        metadata = PackMetadata(
            name='test_pack',
            version='1.0.0',
            description='Test pack',
            vendor='Test Co',
            license='MIT',
            compatibility='2.0.0',
            domain='testing',
            pricing_tier='free'
        )
        
        assert metadata.name == 'test_pack'
        assert metadata.version == '1.0.0'
        assert metadata.description == 'Test pack'
        assert metadata.vendor == 'Test Co'
        assert metadata.license == 'MIT'
        assert metadata.compatibility == '2.0.0'
        assert metadata.domain == 'testing'
        assert metadata.pricing_tier == 'free'
    
    def test_pack_metadata_with_optional_fields(self):
        """Test PackMetadata with optional fields."""
        metadata = PackMetadata(
            name='test_pack',
            version='1.0.0',
            description='Test pack',
            vendor='Test Co',
            license='MIT',
            compatibility='2.0.0',
            domain='testing',
            tags=['test', 'example'],
            pricing_tier='basic'
        )
        
        assert metadata.compatibility == '2.0.0'
        assert metadata.license == 'MIT'
        assert metadata.tags == ['test', 'example']
        assert metadata.pricing_tier == 'basic'


class TestConnectionConfig:
    """Test ConnectionConfig model."""
    
    def test_rest_connection_config(self):
        """Test REST connection configuration."""
        auth = AuthConfig(method=AuthMethod.BEARER, config={'token': 'test_token'})
        
        connection = ConnectionConfig(
            type='rest',
            base_url='https://api.test.com',
            timeout=30,
            auth=auth
        )
        
        assert connection.type == 'rest'
        assert connection.base_url == 'https://api.test.com'
        assert connection.timeout == 30
        assert connection.auth.method == AuthMethod.BEARER
        assert connection.auth.config['token'] == 'test_token'
    
    def test_database_connection_config(self):
        """Test database connection configuration."""
        auth = AuthConfig(method=AuthMethod.BASIC, config={'username': 'user', 'password': 'pass'})
        
        connection = ConnectionConfig(
            type='database',
            engine='postgresql',
            host='db.test.com',
            port=5432,
            database='testdb',
            auth=auth
        )
        
        assert connection.type == 'database'
        assert connection.engine == 'postgresql'
        assert connection.host == 'db.test.com'
        assert connection.port == 5432
        assert connection.database == 'testdb'
    
    def test_ssh_connection_config(self):
        """Test SSH connection configuration."""
        auth = AuthConfig(method=AuthMethod.SSH_KEY, config={'private_key': '/path/to/key'})
        
        connection = ConnectionConfig(
            type='ssh',
            hostname='server.test.com',
            username='testuser',
            port=22,
            auth=auth
        )
        
        assert connection.type == 'ssh'
        assert connection.hostname == 'server.test.com'
        assert connection.username == 'testuser'
        assert connection.port == 22


class TestAuthConfig:
    """Test AuthConfig model."""
    
    def test_bearer_auth(self):
        """Test Bearer token authentication."""
        auth = AuthConfig(method=AuthMethod.BEARER, config={'token': 'bearer_token'})
        
        assert auth.method == AuthMethod.BEARER
        assert auth.config['token'] == 'bearer_token'
    
    def test_basic_auth(self):
        """Test Basic authentication."""
        auth = AuthConfig(
            method=AuthMethod.BASIC,
            config={
                'username': 'testuser',
                'password': 'testpass'
            }
        )
        
        assert auth.method == AuthMethod.BASIC
        assert auth.config['username'] == 'testuser'
        assert auth.config['password'] == 'testpass'
    
    def test_api_key_auth(self):
        """Test API Key authentication."""
        auth = AuthConfig(
            method=AuthMethod.API_KEY,
            config={
                'api_key': 'test_api_key',
                'header_name': 'X-API-Key'
            }
        )
        
        assert auth.method == AuthMethod.API_KEY
        assert auth.config['api_key'] == 'test_api_key'
        assert auth.config['header_name'] == 'X-API-Key'
    
    def test_oauth_auth(self):
        """Test OAuth authentication."""
        auth = AuthConfig(
            method=AuthMethod.OAUTH2,
            config={
                'client_id': 'client123',
                'client_secret': 'secret123',
                'oauth_url': 'https://oauth.test.com'
            }
        )
        
        assert auth.method == AuthMethod.OAUTH2
        assert auth.config['client_id'] == 'client123'
        assert auth.config['client_secret'] == 'secret123'
        assert auth.config['oauth_url'] == 'https://oauth.test.com'


class TestToolDefinition:
    """Test ToolDefinition model."""
    
    def test_list_tool_definition(self):
        """Test list tool definition."""
        from catalyst_pack_schemas.models import ParameterDefinition
        
        param = ParameterDefinition(
            name='limit',
            type='integer',
            required=False,
            default=10,
            description='Number of items to return'
        )
        
        tool = ToolDefinition(
            type=ToolType.LIST,
            description='List items from API',
            endpoint='/api/items',
            method='GET',
            parameters=[param]
        )
        
        assert tool.type == ToolType.LIST
        assert tool.description == 'List items from API'
        assert tool.endpoint == '/api/items'
        assert tool.method == 'GET'
        assert len(tool.parameters) == 1
        assert tool.parameters[0].name == 'limit'
    
    def test_search_tool_definition(self):
        """Test search tool definition."""
        from catalyst_pack_schemas.models import ParameterDefinition
        
        param = ParameterDefinition(
            name='query',
            type='string',
            required=True,
            description='Search query'
        )
        
        tool = ToolDefinition(
            type=ToolType.SEARCH,
            description='Search for items',
            endpoint='/api/search',
            method='POST',
            parameters=[param]
        )
        
        assert tool.type == ToolType.SEARCH
        assert tool.description == 'Search for items'
        assert tool.endpoint == '/api/search'
        assert tool.method == 'POST'
        assert tool.parameters[0].required is True
    
    def test_query_tool_definition(self):
        """Test database query tool definition."""
        from catalyst_pack_schemas.models import ParameterDefinition
        
        param = ParameterDefinition(
            name='table_name',
            type='string',
            required=True,
            description='Table to query'
        )
        
        tool = ToolDefinition(
            type=ToolType.QUERY,
            description='Query database table',
            sql='SELECT * FROM {table_name} LIMIT 100',
            parameters=[param]
        )
        
        assert tool.type == ToolType.QUERY
        assert tool.description == 'Query database table'
        assert tool.sql == 'SELECT * FROM {table_name} LIMIT 100'
    
    def test_command_tool_definition(self):
        """Test command tool definition."""
        from catalyst_pack_schemas.models import ParameterDefinition
        
        param = ParameterDefinition(
            name='filename',
            type='string',
            required=True,
            description='File to process'
        )
        
        tool = ToolDefinition(
            type=ToolType.COMMAND,
            description='Process file',
            command='process_file {filename}',
            parameters=[param]
        )
        
        assert tool.type == ToolType.COMMAND
        assert tool.description == 'Process file'
        assert tool.command == 'process_file {filename}'


class TestPromptDefinition:
    """Test PromptDefinition model."""
    
    def test_prompt_definition_creation(self):
        """Test creating PromptDefinition instance."""
        prompt = PromptDefinition(
            name='Analysis Prompt',
            description='Analyze data and provide insights',
            template='Please analyze the following data: {data}\n\nProvide insights on: {focus_areas}'
        )
        
        assert prompt.name == 'Analysis Prompt'
        assert prompt.description == 'Analyze data and provide insights'
        assert 'analyze the following data' in prompt.template
        assert '{data}' in prompt.template
        assert '{focus_areas}' in prompt.template
    
    def test_prompt_with_variables(self):
        """Test prompt with variables."""
        prompt = PromptDefinition(
            name='Report Prompt',
            description='Generate reports',
            template='Generate a {report_type} report for {time_period}',
            variables=['report_type', 'time_period']
        )
        
        assert prompt.variables == ['report_type', 'time_period']


class TestResourceDefinition:
    """Test ResourceDefinition model."""
    
    def test_documentation_resource(self):
        """Test documentation resource definition."""
        resource = ResourceDefinition(
            name='API Documentation',
            description='Complete API reference',
            type='documentation',
            url='https://docs.api.test.com'
        )
        
        assert resource.name == 'API Documentation'
        assert resource.description == 'Complete API reference'
        assert resource.type == 'documentation'
        assert resource.url == 'https://docs.api.test.com'
    
    def test_tutorial_resource(self):
        """Test tutorial resource definition."""
        resource = ResourceDefinition(
            name='Getting Started Tutorial',
            description='Step-by-step tutorial',
            type='tutorial',
            url='https://tutorial.test.com',
            metadata={'difficulty': 'beginner', 'duration': '30 minutes'}
        )
        
        assert resource.type == 'tutorial'
        assert resource.metadata['difficulty'] == 'beginner'
        assert resource.metadata['duration'] == '30 minutes'


class TestPackModel:
    """Test Pack model."""
    
    def test_pack_creation_from_dict(self, sample_pack_data):
        """Test creating Pack from dictionary."""
        pack = Pack.from_dict(sample_pack_data)
        
        assert pack.metadata.name == 'test_pack'
        assert pack.metadata.version == '1.0.0'
        assert pack.connection.type == 'rest'
        assert pack.connection.base_url == '${API_BASE_URL}'
        assert 'test_tool' in pack.tools
        assert 'test_prompt' in pack.prompts
        assert 'test_docs' in pack.resources
    
    def test_pack_creation_from_yaml_string(self, sample_pack_data):
        """Test creating Pack from YAML string."""
        yaml_string = yaml.dump(sample_pack_data)
        pack = Pack.from_yaml_string(yaml_string)
        
        assert pack.metadata.name == 'test_pack'
        assert pack.connection.type == 'rest'
    
    def test_pack_creation_from_yaml_file(self, create_test_pack):
        """Test creating Pack from YAML file."""
        pack_dir = create_test_pack('yaml_file_test')
        pack_yaml = pack_dir / 'pack.yaml'
        
        pack = Pack.from_yaml_file(str(pack_yaml))
        
        assert pack.metadata.name == 'yaml_file_test'
        assert pack.connection.type == 'rest'
    
    def test_pack_to_dict(self, sample_pack_data):
        """Test converting Pack to dictionary."""
        pack = Pack.from_dict(sample_pack_data)
        pack_dict = pack.to_dict()
        
        assert isinstance(pack_dict, dict)
        assert 'metadata' in pack_dict
        assert 'connection' in pack_dict
        assert pack_dict['metadata']['name'] == 'test_pack'
    
    def test_pack_to_yaml_string(self, sample_pack_data):
        """Test converting Pack to YAML string."""
        pack = Pack.from_dict(sample_pack_data)
        yaml_string = pack.to_yaml_string()
        
        assert isinstance(yaml_string, str)
        assert 'metadata:' in yaml_string
        assert 'name: test_pack' in yaml_string
    
    def test_pack_save_to_file(self, sample_pack_data, temp_dir):
        """Test saving Pack to file."""
        pack = Pack.from_dict(sample_pack_data)
        output_file = temp_dir / 'saved_pack.yaml'
        
        pack.save_to_file(str(output_file))
        
        assert output_file.exists()
        
        # Verify we can load it back
        loaded_pack = Pack.from_yaml_file(str(output_file))
        assert loaded_pack.metadata.name == 'test_pack'
    
    def test_modular_pack_creation(self, sample_modular_pack_data):
        """Test creating modular pack with structure."""
        pack = Pack.from_dict(sample_modular_pack_data)
        
        assert pack.metadata.name == 'modular_test_pack'
        assert pack.structure is not None
        assert 'tools' in pack.structure
        assert len(pack.structure['tools']) == 2


class TestPackValidationError:
    """Test PackValidationError exception."""
    
    def test_pack_validation_error(self):
        """Test PackValidationError creation."""
        error = PackValidationError("Test validation error")
        
        assert str(error) == "Test validation error"
        assert isinstance(error, Exception)
    
    def test_pack_validation_error_with_details(self):
        """Test PackValidationError with error details."""
        errors = ['Error 1', 'Error 2']
        error = PackValidationError("Validation failed", errors=errors)
        
        assert str(error) == "Validation failed"
        assert error.errors == errors


class TestEnums:
    """Test enum classes."""
    
    def test_tool_type_enum(self):
        """Test ToolType enum values."""
        assert ToolType.LIST.value == 'list'
        assert ToolType.DETAILS.value == 'details'
        assert ToolType.SEARCH.value == 'search'
        assert ToolType.EXECUTE.value == 'execute'
        assert ToolType.QUERY.value == 'query'
        assert ToolType.COMMAND.value == 'command'
    
    def test_auth_method_enum(self):
        """Test AuthMethod enum values."""
        assert AuthMethod.BEARER.value == 'bearer'
        assert AuthMethod.BASIC.value == 'basic'
        assert AuthMethod.API_KEY.value == 'api_key'
        assert AuthMethod.OAUTH2.value == 'oauth2'
        assert AuthMethod.SSH_KEY.value == 'ssh_key'
        assert AuthMethod.PASSTHROUGH.value == 'passthrough'


class TestParameterDefinition:
    """Test ParameterDefinition model."""
    
    def test_required_parameter(self):
        """Test required parameter definition."""
        from catalyst_pack_schemas.models import ParameterDefinition
        
        param = ParameterDefinition(
            name='query',
            type='string',
            required=True,
            description='Search query'
        )
        
        assert param.name == 'query'
        assert param.type == 'string'
        assert param.required is True
        assert param.description == 'Search query'
        assert param.default is None
    
    def test_optional_parameter_with_default(self):
        """Test optional parameter with default value."""
        from catalyst_pack_schemas.models import ParameterDefinition
        
        param = ParameterDefinition(
            name='limit',
            type='integer',
            required=False,
            default=10,
            description='Number of results'
        )
        
        assert param.name == 'limit'
        assert param.type == 'integer'
        assert param.required is False
        assert param.default == 10
    
    def test_parameter_with_choices(self):
        """Test parameter with limited choices."""
        from catalyst_pack_schemas.models import ParameterDefinition
        
        param = ParameterDefinition(
            name='format',
            type='string',
            required=False,
            default='json',
            description='Output format',
            choices=['json', 'xml', 'csv']
        )
        
        assert param.choices == ['json', 'xml', 'csv']
        assert param.default == 'json'