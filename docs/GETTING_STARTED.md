# Getting Started with Catalyst

Create your first AI-powered business integration in under 10 minutes.

## Prerequisites

- Python 3.8 or higher
- Access to a business system (API, database, or file system)
- Catalyst MCP Server ([Get it here](https://github.com/billebel/catalyst))

## Step 1: Install Catalyst Pack Builder

```bash
pip install catalyst-pack-schemas
```

Verify installation:
```bash
catalyst-packs --help
```

## Step 2: Create Your First Pack

Let's create a Salesforce CRM integration as an example:

```bash
catalyst-packs create salesforce-crm \
  --type rest \
  --description "Salesforce CRM integration for sales team"
```

This creates:
```
salesforce-crm/
├── pack.yaml          # Main configuration
├── tools/             # Tool definitions
├── prompts/           # AI prompt templates  
├── resources/         # Documentation
└── README.md          # Pack documentation
```

## Step 3: Configure Your Connection

Edit `salesforce-crm/pack.yaml`:

```yaml
metadata:
  name: salesforce-crm
  version: 1.0.0
  description: "Salesforce CRM integration for sales team"
  vendor: "Your Company"
  domain: crm

connection:
  type: rest
  base_url: "https://your-instance.salesforce.com/services/data/v58.0"
  auth:
    method: bearer
    token: "${SALESFORCE_TOKEN}"
  timeout: 30
  rate_limit:
    requests_per_minute: 100

tools:
  - name: search_accounts
    type: search
    description: "Search for accounts by name or industry"
    endpoint: "/sobjects/Account"
    parameters:
      query:
        type: string
        description: "Search query (name or industry)"
        required: true
    transform:
      engine: jq
      script: ".records[] | {id: .Id, name: .Name, industry: .Industry}"
```

## Step 4: Set Up Authentication

Create environment file `.env`:
```bash
# Salesforce credentials
SALESFORCE_TOKEN=your_salesforce_api_token_here
```

**Security Note**: Never commit credentials to version control.

## Step 5: Validate Your Pack

```bash
catalyst-packs validate salesforce-crm/
```

Expected output:
```
✅ Pack validation successful
- Metadata: Valid
- Connection: Valid  
- Tools: 1 tool validated
- Security: No credentials exposed
```

## Step 6: Install to Catalyst MCP Server

```bash
# Install pack for AI use
catalyst-packs install salesforce-crm/
```

This makes your tools available to AI assistants through the MCP protocol.

## Step 7: Test with AI Assistant

In Claude Desktop or compatible AI assistant:

**User**: "Search for technology companies in Salesforce"

**AI Response**: 
```
I'll search for technology companies in your Salesforce CRM.

[Uses search_accounts tool with query="technology"]

Found 12 technology companies:
- ACME Tech Solutions (Software)
- DataCorp Systems (Technology)  
- CloudVision Inc (Cloud Services)
...
```

## What Just Happened?

1. **Configuration**: You defined your integration in simple YAML
2. **Security**: Credentials stored securely in environment variables
3. **Validation**: Automatic testing ensured everything works
4. **Deployment**: Pack installed to MCP server in one command
5. **AI Integration**: AI can now access your Salesforce data directly

## Next Steps

### Add More Tools
```yaml
tools:
  - name: create_contact
    type: execute
    method: POST
    endpoint: "/sobjects/Contact"
    description: "Create new contact"
    
  - name: get_opportunities  
    type: list
    endpoint: "/sobjects/Opportunity"
    description: "List sales opportunities"
```

### Add Business Logic
```yaml
tools:
  - name: quarterly_sales_report
    type: query
    description: "Generate Q4 sales report"
    sql: |
      SELECT Account.Name, SUM(Opportunity.Amount) as Total
      FROM Opportunity 
      JOIN Account ON Opportunity.AccountId = Account.Id
      WHERE Opportunity.CloseDate >= {start_date}
      GROUP BY Account.Name
      ORDER BY Total DESC
```

### Customize AI Prompts
```yaml
prompts:
  - name: sales_assistant
    description: "AI assistant for sales team"
    content: |
      You are a sales assistant with access to Salesforce CRM.
      Help users find accounts, create contacts, and track opportunities.
      Always confirm before making changes to data.
    suggested_tools: [search_accounts, create_contact, get_opportunities]
```

## Common Integration Types

### REST API Integration
Perfect for: Salesforce, HubSpot, Stripe, GitHub, Slack
- Authentication: Bearer, OAuth2, API Key, Basic Auth
- Operations: GET, POST, PUT, DELETE with full parameter support
- Response transformation with jq, JavaScript, or Python

### Database Integration  
Perfect for: PostgreSQL, MySQL, SQL Server, MongoDB
- Secure connection pooling and query optimization
- Parameterized queries with SQL injection protection
- Support for complex joins, aggregations, and analytics

### File System Integration
Perfect for: AWS S3, Azure Blob, Google Cloud Storage, SharePoint
- Upload, download, list, and search operations
- Metadata extraction and content analysis
- Batch operations and synchronization

## Best Practices

### Security
- ✅ Use environment variables for credentials
- ✅ Enable rate limiting for API protection  
- ✅ Validate all input parameters
- ✅ Use least-privilege access patterns

### Performance
- ✅ Implement request caching where appropriate
- ✅ Use pagination for large data sets
- ✅ Set reasonable timeouts and retries
- ✅ Monitor API rate limits

### Maintainability
- ✅ Use clear, descriptive tool names
- ✅ Add comprehensive parameter descriptions
- ✅ Include example usage in documentation
- ✅ Version your packs semantically

## Troubleshooting

### Common Issues

**Pack validation fails**
```bash
# Check detailed validation errors
catalyst-packs validate salesforce-crm/ --verbose
```

**Authentication errors**
```bash
# Test connection separately  
curl -H "Authorization: Bearer $SALESFORCE_TOKEN" \
  "https://your-instance.salesforce.com/services/data/v58.0/sobjects"
```

**AI can't access tools**
```bash
# Verify pack installation
catalyst-packs list --installed
```

### Getting Help

- [CLI Reference](CLI_REFERENCE.md) - Complete command documentation
- [Integration Patterns](INTEGRATION_PATTERNS.md) - Common examples
- [Security Guide](SECURITY.md) - Authentication best practices
- [GitHub Issues](https://github.com/billebel/catalyst-pack-schemas/issues) - Report problems

---

**Congratulations!** You've created your first AI-powered business integration.

**Next**: Explore [Integration Patterns](INTEGRATION_PATTERNS.md) for more advanced examples.