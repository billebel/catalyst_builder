# CLI Reference

Complete command-line interface reference for Catalyst Pack Builder.

## Installation and Setup

```bash
# Install from PyPI
pip install catalyst-pack-schemas

# Verify installation
catalyst-packs --version

# Get help
catalyst-packs --help
```

## Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--verbose`, `-v` | Enable verbose output | `false` |
| `--quiet`, `-q` | Suppress non-error output | `false` |
| `--config FILE` | Use custom configuration file | `~/.catalyst/config.yml` |
| `--no-color` | Disable colored output | `false` |

## Commands

### `create` - Create New Pack

Create a new Knowledge Pack from templates.

```bash
catalyst-packs create <name> [options]
```

#### Options
| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `<name>` | Pack name (alphanumeric, hyphens) | ✅ | - |
| `--type`, `-t` | Connection type | ✅ | `rest` |
| `--description`, `-d` | Pack description | ❌ | Auto-generated |
| `--vendor`, `-v` | Pack vendor/author | ❌ | Current user |
| `--domain` | Business domain | ❌ | `general` |
| `--output`, `-o` | Output directory | ❌ | Current directory |

#### Connection Types
- `rest` - REST API integration
- `database` - Database connection (PostgreSQL, MySQL, etc.)
- `ssh` - SSH/shell command execution
- `filesystem` - File system operations (S3, local, etc.)
- `message_queue` - Message queue integration (RabbitMQ, Kafka)

#### Examples
```bash
# Basic REST API pack
catalyst-packs create salesforce-api --type rest --description "Salesforce CRM integration"

# Database analytics pack
catalyst-packs create analytics-db --type database --domain analytics --vendor "Analytics Team"

# SSH operations pack
catalyst-packs create server-ops --type ssh --domain devops

# Custom output directory
catalyst-packs create my-pack --type rest --output ./packs/
```

### `validate` - Validate Pack Configuration

Validate pack files and directory structure.

```bash
catalyst-packs validate <path> [options]
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `<path>` | Pack directory or file to validate | Current directory |
| `--summary` | Show only validation summary | `false` |
| `--json` | Output results in JSON format | `false` |
| `--strict` | Treat warnings as errors | `false` |
| `--check-endpoints` | Test API endpoints if possible | `false` |

#### Examples
```bash
# Validate single pack
catalyst-packs validate ./my-pack/

# Validate all packs in directory
catalyst-packs validate ./packs/ --summary

# Strict validation with endpoint testing
catalyst-packs validate ./my-pack/ --strict --check-endpoints

# JSON output for automation
catalyst-packs validate ./my-pack/ --json > validation-report.json
```

#### Exit Codes
- `0` - All validations passed
- `1` - Validation errors found
- `2` - Configuration or system error

### `install` - Install Pack for AI Use

Install pack to make it available to AI assistants via MCP server.

```bash
catalyst-packs install <pack> [options]
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `<pack>` | Pack directory, file, or URL | - |
| `--target`, `-t` | Installation target | Auto-detect |
| `--mode`, `-m` | Installation mode | `development` |
| `--name` | Override pack name | Pack metadata name |
| `--force` | Force reinstall if exists | `false` |
| `--no-validate` | Skip validation before install | `false` |
| `--env-file` | Environment file to use | `.env` |

#### Installation Modes
- `development` - Install with debug symbols, reload on changes
- `staging` - Install with staging configuration
- `production` - Install optimized for production use

#### Examples
```bash
# Install local pack
catalyst-packs install ./my-pack/

# Install from URL
catalyst-packs install https://github.com/user/pack.git

# Install to specific target
catalyst-packs install ./my-pack/ --target /opt/catalyst/packs/

# Production installation
catalyst-packs install ./my-pack/ --mode production --force
```

### `list` - List Available Packs

List installed or available packs.

```bash
catalyst-packs list [path] [options]
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `[path]` | Directory to search | Current directory |
| `--installed` | Show only installed packs | `false` |
| `--available` | Show available but not installed | `false` |
| `--format`, `-f` | Output format | `table` |
| `--sort` | Sort by field | `name` |
| `--filter` | Filter by domain or vendor | - |

#### Output Formats
- `table` - Human-readable table
- `json` - JSON array
- `csv` - CSV format
- `yaml` - YAML format

#### Examples
```bash
# List all packs in current directory
catalyst-packs list

# List only installed packs  
catalyst-packs list --installed

# List packs in JSON format
catalyst-packs list --format json

# Filter by domain
catalyst-packs list --filter domain=crm

# Sort by version
catalyst-packs list --sort version
```

### `init` - Initialize Pack Development Project

Initialize directory structure for pack development.

```bash
catalyst-packs init [directory] [options]
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `[directory]` | Project directory | Current directory |
| `--template` | Project template to use | `basic` |
| `--git` | Initialize git repository | `false` |
| `--examples` | Include example packs | `false` |
| `--vscode` | Include VS Code configuration | `false` |

#### Templates
- `basic` - Basic pack development setup
- `enterprise` - Enterprise pack development with CI/CD
- `multi-pack` - Multi-pack repository structure

#### Examples
```bash
# Initialize basic project
catalyst-packs init my-packs-project

# Enterprise setup with examples
catalyst-packs init ./enterprise-packs/ --template enterprise --examples --git

# VS Code integration
catalyst-packs init --vscode --git
```

### `test` - Test Pack Tools

Test individual pack tools with sample data.

```bash
catalyst-packs test <pack> <tool> [options]
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `<pack>` | Pack directory or name | - |
| `<tool>` | Tool name to test | - |
| `--params` | JSON parameter string | `{}` |
| `--env-file` | Environment file | `.env` |
| `--dry-run` | Simulate without actual API calls | `false` |
| `--output`, `-o` | Save output to file | - |

#### Parameter Formats
```bash
# Simple parameters
catalyst-packs test my-pack search_users --params '{"query": "john"}'

# From file
catalyst-packs test my-pack create_user --params @user-data.json

# Interactive mode (prompts for parameters)
catalyst-packs test my-pack search_users --interactive
```

#### Examples
```bash
# Test search tool
catalyst-packs test ./my-pack/ search_customers --params '{"query": "ACME Corp"}'

# Test with dry run
catalyst-packs test ./my-pack/ create_order --params @test-order.json --dry-run

# Save output for analysis
catalyst-packs test ./my-pack/ analytics_report --output report.json
```

### `status` - Show Installation Status

Show status of installed packs and MCP server.

```bash
catalyst-packs status [options]
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `--target`, `-t` | Check specific installation target | All targets |
| `--health` | Perform health checks | `false` |
| `--json` | JSON output format | `false` |
| `--verbose`, `-v` | Show detailed status | `false` |

#### Examples
```bash
# Show status of all installations
catalyst-packs status

# Health check with detailed output
catalyst-packs status --health --verbose

# JSON output for monitoring
catalyst-packs status --json > status-report.json
```

### `uninstall` - Remove Installed Pack

Remove pack from MCP server installation.

```bash
catalyst-packs uninstall <pack> [options]
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `<pack>` | Pack name to uninstall | - |
| `--target`, `-t` | Target installation | Auto-detect |
| `--backup` | Create backup before removal | `true` |
| `--force` | Force removal without confirmation | `false` |

#### Examples
```bash
# Uninstall pack with backup
catalyst-packs uninstall salesforce-api

# Force removal without backup
catalyst-packs uninstall old-pack --force --no-backup

# Remove from specific target
catalyst-packs uninstall my-pack --target /opt/catalyst/
```

## Configuration File

Default configuration file: `~/.catalyst/config.yml`

```yaml
# Default settings
defaults:
  vendor: "Your Company"
  domain: "general"
  license: "MIT"
  
# Installation targets
targets:
  development:
    path: "/home/user/.catalyst/packs/"
    mode: "development"
  production:
    path: "/opt/catalyst/packs/"
    mode: "production"
    backup: true
    
# Validation settings
validation:
  strict: false
  check_endpoints: false
  timeout: 30

# Output preferences  
output:
  color: true
  format: "table"
  verbosity: "normal"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CATALYST_CONFIG` | Configuration file path | `~/.catalyst/config.yml` |
| `CATALYST_PACKS_DIR` | Default packs directory | `./packs/` |
| `CATALYST_MCP_SERVER` | MCP server URL | Auto-detect |
| `CATALYST_LOG_LEVEL` | Logging level | `INFO` |
| `NO_COLOR` | Disable colored output | `false` |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error or validation failure |
| `2` | Configuration error |
| `3` | Network or connectivity error |
| `4` | Permission or authentication error |
| `5` | File system error |

## Examples and Common Workflows

### Complete Development Workflow
```bash
# 1. Initialize project
catalyst-packs init my-integration-project --git --examples

# 2. Create new pack
cd my-integration-project
catalyst-packs create crm-integration --type rest --domain sales

# 3. Edit pack configuration
# (Edit crm-integration/pack.yaml)

# 4. Validate configuration
catalyst-packs validate crm-integration/ --strict

# 5. Test tools
catalyst-packs test crm-integration search_customers --params '{"query": "test"}'

# 6. Install for development
catalyst-packs install crm-integration/ --mode development

# 7. Check status
catalyst-packs status --health

# 8. Deploy to production
catalyst-packs install crm-integration/ --mode production --target production
```

### Batch Operations
```bash
# Validate all packs
find ./packs/ -name "pack.yaml" -exec catalyst-packs validate {} \;

# Install multiple packs
for pack in ./packs/*/; do
  catalyst-packs install "$pack" --mode production
done

# Generate pack inventory
catalyst-packs list --format json > pack-inventory.json
```

### Automation and CI/CD
```bash
# Validation in CI pipeline
catalyst-packs validate ./my-pack/ --json --strict
exit_code=$?
if [ $exit_code -ne 0 ]; then
  echo "Pack validation failed"
  exit $exit_code
fi

# Automated deployment
catalyst-packs install ./my-pack/ --mode production --force --no-validate
```

---

**Next Steps**:
- Review [Getting Started Guide](GETTING_STARTED.md) for step-by-step tutorials
- Explore [Pack Development Guide](PACK_DEVELOPMENT.md) for advanced configuration
- Check [Integration Patterns](INTEGRATION_PATTERNS.md) for common examples