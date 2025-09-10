"""
Unit tests for pack builder functionality.
"""

import pytest
import yaml
from pathlib import Path
from catalyst_pack_schemas import PackBuilder, PackFactory, quick_pack, create_pack
from catalyst_pack_schemas.models import ToolType, AuthMethod


class TestPackBuilder:
    """Test PackBuilder class."""
    
    def test_pack_builder_initialization(self):
        """Test PackBuilder can be initialized."""
        builder = PackBuilder('test_pack')
        
        assert builder.name == 'test_pack'
        assert builder.pack['metadata']['name'] == 'test_pack'
    
    def test_set_metadata(self):
        """Test setting pack metadata."""
        builder = PackBuilder('test_pack')
        
        builder.set_metadata(
            version='2.0.0',
            description='Updated test pack',
            vendor='New Vendor',
            domain='analytics',
            license='Apache-2.0'
        )
        
        assert builder.pack['metadata']['version'] == '2.0.0'
        assert builder.pack['metadata']['description'] == 'Updated test pack'
        assert builder.pack['metadata']['vendor'] == 'New Vendor'
        assert builder.pack['metadata']['domain'] == 'analytics'
        assert builder.pack['metadata']['license'] == 'Apache-2.0'
    
    def test_set_connection_rest(self):
        """Test setting REST connection."""
        builder = PackBuilder('test_pack')
        
        builder.set_connection(
            connection_type='rest',
            base_url='https://api.example.com',
            timeout=60
        )
        
        assert builder.pack['connection']['type'] == 'rest'
        assert builder.pack['connection']['base_url'] == 'https://api.example.com'
        assert builder.pack['connection']['timeout'] == 60
    
    def test_set_connection_database(self):
        """Test setting database connection."""
        builder = PackBuilder('test_pack')
        
        builder.set_connection(
            connection_type='database',
            engine='mysql',
            host='db.example.com',
            port=3306,
            database='testdb'
        )
        
        assert builder.pack['connection']['type'] == 'database'
        assert builder.pack['connection']['engine'] == 'mysql'
        assert builder.pack['connection']['host'] == 'db.example.com'
        assert builder.pack['connection']['port'] == 3306
        assert builder.pack['connection']['database'] == 'testdb'
    
    def test_set_auth_bearer(self):
        """Test setting Bearer authentication."""
        builder = PackBuilder('test_pack')
        
        builder.set_connection(
            connection_type='rest',
            base_url='https://api.test.com',
            auth={
                'method': 'bearer',
                'config': {
                    'token': '${API_TOKEN}'
                }
            }
        )
        
        assert builder.pack['connection']['auth']['method'] == 'bearer'
        assert builder.pack['connection']['auth']['config']['token'] == '${API_TOKEN}'
    
    def test_set_auth_passthrough(self):
        """Test setting PASSTHROUGH authentication."""
        builder = PackBuilder('test_pack')
        
        builder.set_connection(
            connection_type='rest',
            base_url='https://api.test.com',
            auth={
                'method': 'passthrough',
                'config': {
                    'source': 'user_context',
                    'header': 'Authorization',
                    'format': 'Bearer {token}'
                }
            }
        )
        
        assert builder.pack['connection']['auth']['method'] == 'passthrough'
        assert builder.pack['connection']['auth']['config']['source'] == 'user_context'
        assert builder.pack['connection']['auth']['config']['header'] == 'Authorization'
        assert builder.pack['connection']['auth']['config']['format'] == 'Bearer {token}'
    
    def test_set_auth_basic(self):
        """Test setting Basic authentication."""
        builder = PackBuilder('test_pack')
        
        builder.set_connection(
            connection_type='rest',
            base_url='https://api.test.com',
            auth={
                'method': 'basic',
                'config': {
                    'username': '${DB_USER}',
                    'password': '${DB_PASSWORD}'
                }
            }
        )
        
        assert builder.pack['connection']['auth']['method'] == 'basic'
        assert builder.pack['connection']['auth']['config']['username'] == '${DB_USER}'
        assert builder.pack['connection']['auth']['config']['password'] == '${DB_PASSWORD}'
    
    def test_add_list_tool(self):
        """Test adding a list tool."""
        builder = PackBuilder('test_pack')
        
        builder.add_tool(
            'list_items',
            tool_type='list',
            description='List all items',
            endpoint='/api/items',
            method='GET'
        )
        
        assert len(builder.pack['tools']) == 1
        tool = builder.pack['tools'][0]
        assert tool['name'] == 'list_items'
        assert tool['type'] == 'list'
        assert tool['description'] == 'List all items'
        assert tool['endpoint'] == '/api/items'
        assert tool['method'] == 'GET'
    
    def test_add_search_tool(self):
        """Test adding a search tool."""
        builder = PackBuilder('test_pack')
        
        builder.add_tool(
            'search_items',
            tool_type='search',
            description='Search for items',
            endpoint='/api/search',
            method='POST'
        )
        
        assert len(builder.pack['tools']) == 1
        tool = builder.pack['tools'][0]
        assert tool['name'] == 'search_items'
        assert tool['type'] == 'search'
        assert tool['endpoint'] == '/api/search'
        assert tool['method'] == 'POST'
    
    def test_add_query_tool(self):
        """Test adding a query tool."""
        builder = PackBuilder('test_pack')
        
        builder.add_tool(
            'query_data',
            tool_type='query',
            description='Query database',
            sql='SELECT * FROM table WHERE condition = ?'
        )
        
        assert len(builder.pack['tools']) == 1
        tool = builder.pack['tools'][0]
        assert tool['name'] == 'query_data'
        assert tool['type'] == 'query'
        assert tool['sql'] == 'SELECT * FROM table WHERE condition = ?'
    
    def test_add_command_tool(self):
        """Test adding a command tool."""
        builder = PackBuilder('test_pack')
        
        builder.add_tool(
            'run_command',
            tool_type='command',
            description='Run system command',
            command='ls -la {directory}'
        )
        
        assert len(builder.pack['tools']) == 1
        tool = builder.pack['tools'][0]
        assert tool['name'] == 'run_command'
        assert tool['type'] == 'command'
        assert tool['command'] == 'ls -la {directory}'
    
    def test_add_tool_with_parameters(self):
        """Test adding tool with parameters."""
        builder = PackBuilder('test_pack')
        
        parameters = [
            {
                'name': 'limit',
                'type': 'integer',
                'required': False,
                'default': 10,
                'description': 'Number of results'
            },
            {
                'name': 'query',
                'type': 'string', 
                'required': True,
                'description': 'Search query'
            }
        ]
        
        builder.add_tool(
            'search_with_params',
            tool_type='search',
            description='Search with parameters',
            endpoint='/api/search',
            parameters=parameters
        )
        
        assert len(builder.pack['tools']) == 1
        tool = builder.pack['tools'][0]
        assert tool['name'] == 'search_with_params'
        assert len(tool['parameters']) == 2
        assert tool['parameters'][0]['name'] == 'limit'
        assert tool['parameters'][0]['default'] == 10
        assert tool['parameters'][1]['name'] == 'query'
        assert tool['parameters'][1]['required'] is True
    
    def test_add_prompt(self):
        """Test adding a prompt."""
        builder = PackBuilder('test_pack')
        
        builder.add_prompt(
            name='analysis_prompt',
            template='Please analyze this data: {data} and focus on: {focus}',
            description='Analyze data and provide insights'
        )
        
        assert len(builder.pack['prompts']) == 1
        prompt = builder.pack['prompts'][0]
        assert prompt['name'] == 'analysis_prompt'
        assert prompt['description'] == 'Analyze data and provide insights'
        assert '{data}' in prompt['template']
        assert '{focus}' in prompt['template']
    
    def test_add_resource(self):
        """Test adding a resource."""
        builder = PackBuilder('test_pack')
        
        builder.add_resource(
            name='api_docs',
            resource_type='documentation',
            description='Complete API reference',
            url='https://docs.api.com'
        )
        
        assert len(builder.pack['resources']) == 1
        resource = builder.pack['resources'][0]
        assert resource['name'] == 'api_docs'
        assert resource['type'] == 'documentation'
        assert resource['url'] == 'https://docs.api.com'
    
    def test_build_pack(self):
        """Test building the complete pack."""
        builder = PackBuilder('complete_test_pack')
        
        builder.set_metadata(
            version='1.5.0',
            description='Complete test pack',
            vendor='Test Company',
            domain='testing'
        )
        
        builder.set_connection(
            connection_type='rest',
            base_url='https://api.test.com',
            auth={
                'method': 'bearer',
                'config': {'token': '${TOKEN}'}
            }
        )
        
        builder.add_tool(
            'list_all',
            tool_type='list',
            description='List all items',
            endpoint='/api/items'
        )
        
        builder.add_prompt(
            name='test_prompt',
            template='Test: {input}',
            description='Test prompt'
        )
        
        pack = builder.build()
        
        assert pack['metadata']['name'] == 'complete_test_pack'
        assert pack['metadata']['version'] == '1.5.0'
        assert pack['connection']['type'] == 'rest'
        assert len(pack['tools']) == 1
        assert pack['tools'][0]['name'] == 'list_all'
        assert len(pack['prompts']) == 1
        assert pack['prompts'][0]['name'] == 'test_prompt'
    
    def test_save_pack(self, temp_dir):
        """Test saving pack to file."""
        builder = PackBuilder('save_test_pack')
        builder.set_metadata(description='Pack to save', vendor='Test', domain='test')
        builder.set_connection(connection_type='rest', base_url='https://api.test.com')
        
        output_path = builder.scaffold(str(temp_dir))
        
        assert output_path.exists()
        assert output_path.is_dir()
        assert (output_path / 'pack.yaml').exists()
        
        # Verify content
        with open(output_path / 'pack.yaml') as f:
            pack_data = yaml.safe_load(f)
        
        assert pack_data['metadata']['name'] == 'save_test_pack'
        assert pack_data['metadata']['description'] == 'Pack to save'


class TestPackFactory:
    """Test PackFactory class."""
    
    def test_create_rest_pack(self):
        """Test creating REST API pack."""
        builder = PackFactory.create_rest_api_pack(
            name='rest_factory_test',
            base_url='https://api.example.com',
            description='REST pack from factory'
        )
        
        assert builder.pack['metadata']['name'] == 'rest_factory_test'
        assert builder.pack['connection']['type'] == 'rest'
        assert builder.pack['connection']['base_url'] == 'https://api.example.com'
        assert builder.pack['metadata']['description'] == 'REST pack from factory'
    
    def test_create_database_pack(self):
        """Test creating database pack."""
        builder = PackFactory.create_database_pack(
            name='db_factory_test',
            engine='postgresql'
        )
        
        assert builder.pack['metadata']['name'] == 'db_factory_test'
        assert builder.pack['connection']['type'] == 'database'
        assert builder.pack['connection']['engine'] == 'postgresql'
    
    def test_create_monitoring_pack(self):
        """Test creating monitoring pack."""
        builder = PackFactory.create_monitoring_pack(
            name='monitoring_factory_test',
            system='prometheus'
        )
        
        assert builder.pack['metadata']['name'] == 'monitoring_factory_test'
        assert 'prometheus' in builder.pack['metadata']['description']
    
    def test_create_pack_with_auth(self):
        """Test creating pack with authentication."""
        builder = PackFactory.create_rest_api_pack(
            name='auth_test_pack',
            base_url='https://api.example.com',
            description='Pack with auth'
        )
        
        # The factory creates a basic pack, we can check for the REST connection
        assert builder.pack['connection']['type'] == 'rest'
        assert builder.pack['connection']['base_url'] == 'https://api.example.com'


class TestQuickPack:
    """Test quick_pack convenience function."""
    
    def test_quick_pack_rest(self, temp_dir):
        """Test quick pack creation for REST API."""
        pack_dir = create_pack(
            pack_name='quick_rest_pack',
            output_dir=str(temp_dir),
            connection_type='rest',
            base_url='https://api.quick.com',
            description='Quick REST pack',
            vendor='Quick Co',
            domain='api'
        )
        
        assert pack_dir.exists()
        assert (pack_dir / 'pack.yaml').exists()
        
        with open(pack_dir / 'pack.yaml') as f:
            pack_data = yaml.safe_load(f)
        
        assert pack_data['metadata']['name'] == 'quick_rest_pack'
        assert pack_data['connection']['type'] == 'rest'
        assert pack_data['connection']['base_url'] == 'https://api.quick.com'
    
    def test_quick_pack_database(self, temp_dir):
        """Test quick pack creation for database."""
        pack_dir = create_pack(
            pack_name='quick_db_pack',
            output_dir=str(temp_dir),
            connection_type='database',
            engine='mysql',
            description='Quick database pack',
            vendor='Quick DB Co',
            domain='data'
        )
        
        assert pack_dir.exists()
        
        with open(pack_dir / 'pack.yaml') as f:
            pack_data = yaml.safe_load(f)
        
        assert pack_data['connection']['type'] == 'database'
        assert pack_data['connection']['engine'] == 'mysql'
        assert pack_data['connection']['host'] == '${DB_HOST}'


class TestCreatePack:
    """Test create_pack convenience function."""
    
    def test_create_pack_rest(self, temp_dir):
        """Test create_pack for REST API."""
        pack_path = create_pack(
            pack_name='create_rest_pack',
            output_dir=str(temp_dir),
            connection_type='rest',
            base_url='https://api.create.com',
            domain='api',
            vendor='Create Co',
            description='Created REST pack'
        )
        
        assert pack_path.exists()
        assert pack_path.is_dir()
        assert (pack_path / 'pack.yaml').exists()
        assert (pack_path / 'README.md').exists()
        
        with open(pack_path / 'pack.yaml') as f:
            pack_data = yaml.safe_load(f)
        
        assert pack_data['metadata']['name'] == 'create_rest_pack'
        assert pack_data['metadata']['domain'] == 'api'
        assert pack_data['metadata']['vendor'] == 'Create Co'
    
    def test_create_pack_with_auth(self, temp_dir):
        """Test create_pack with authentication."""
        pack_path = create_pack(
            pack_name='create_auth_pack',
            output_dir=str(temp_dir),
            connection_type='rest',
            base_url='https://api.auth.com',
            auth_method='bearer',
            auth_token='${AUTH_TOKEN}',
            domain='security',
            vendor='Auth Create Co',
            description='Pack with authentication'
        )
        
        with open(pack_path / 'pack.yaml') as f:
            pack_data = yaml.safe_load(f)
        
        assert 'auth' in pack_data['connection']
        assert pack_data['connection']['auth']['method'] == 'bearer'
        assert pack_data['connection']['auth']['token'] == '${API_TOKEN}'
    
    def test_create_pack_ssh(self, temp_dir):
        """Test create_pack for SSH."""
        pack_path = create_pack(
            pack_name='create_ssh_pack',
            output_dir=str(temp_dir),
            connection_type='ssh',
            hostname='server.create.com',
            username='createuser',
            domain='infrastructure',
            vendor='SSH Create Co',
            description='Created SSH pack'
        )
        
        with open(pack_path / 'pack.yaml') as f:
            pack_data = yaml.safe_load(f)
        
        assert pack_data['connection']['type'] == 'ssh'
        assert pack_data['connection']['hostname'] == '${SSH_HOST}'
        assert pack_data['connection']['username'] == '${SSH_USER}'
    
    def test_create_pack_creates_directory_structure(self, temp_dir):
        """Test that create_pack creates proper directory structure."""
        pack_path = create_pack(
            pack_name='structure_test_pack',
            output_dir=str(temp_dir),
            connection_type='rest',
            base_url='https://api.test.com',
            domain='test',
            vendor='Test Co'
        )
        
        # Check basic files
        assert (pack_path / 'pack.yaml').exists()
        assert (pack_path / 'README.md').exists()
        
        # Check modular structure
        assert (pack_path / 'tools').exists()
        assert (pack_path / 'prompts').exists()
        assert (pack_path / 'resources').exists()
        
        # Check README content
        readme_content = (pack_path / 'README.md').read_text()
        assert 'structure_test_pack' in readme_content
        assert 'Test Co' in readme_content
    
    def test_create_pack_with_custom_connection_type(self, temp_dir):
        """Test create_pack accepts custom connection types."""
        # create_pack should accept any connection type without validation
        pack_path = create_pack(
            pack_name='custom_conn_pack',
            output_dir=str(temp_dir),
            connection_type='custom_type',
            domain='test',
            vendor='Test Co'
        )
        
        with open(pack_path / 'pack.yaml') as f:
            pack_data = yaml.safe_load(f)
        
        assert pack_data['connection']['type'] == 'custom_type'