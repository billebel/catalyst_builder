# Pack Development Guide

Complete guide to creating, testing, and deploying Catalyst Knowledge Packs.

## Pack Structure

### Basic Pack Layout
```
my-pack/
├── pack.yaml              # Main pack configuration
├── tools/                 # Tool definitions (modular packs)
│   ├── search.yaml
│   ├── create.yaml  
│   └── analytics.yaml
├── prompts/               # AI prompt templates
│   └── assistant.yaml
├── resources/             # Documentation and references
│   ├── api-docs.md
│   └── examples.md
├── transforms/            # Response transformation scripts
│   ├── format_results.jq
│   └── clean_data.py
└── README.md             # Pack documentation
```

### Monolithic vs Modular

**Monolithic Pack** (≤5 tools):
```yaml
# pack.yaml contains everything
metadata: {...}
connection: {...}
tools: [...] 
prompts: [...]
```

**Modular Pack** (>5 tools):
```yaml
# pack.yaml
metadata: {...}
connection: {...}
structure:
  tools: "./tools/"
  prompts: "./prompts/"  
  resources: "./resources/"
```

## Pack Configuration (pack.yaml)

### Complete Example
```yaml
metadata:
  name: enterprise-crm
  version: 1.2.0
  description: "Enterprise CRM with AI-powered insights"
  vendor: "ACME Corporation"
  domain: customer_relationship_management
  license: MIT
  compatibility: ">=1.0.0"
  tags: [crm, sales, enterprise]
  
connection:
  type: rest
  base_url: "${CRM_BASE_URL}"
  auth:
    method: oauth2
    config:
      client_id: "${CRM_CLIENT_ID}"
      client_secret: "${CRM_CLIENT_SECRET}"
      token_url: "${CRM_BASE_URL}/oauth/token"
      scopes: [read, write]
  timeout: 30
  rate_limit:
    requests_per_minute: 120
    burst_allowance: 10
  retry_policy:
    max_attempts: 3
    backoff_strategy: exponential
    
tools:
  - name: search_customers
    type: search
    description: "Search customers by name, email, or company"
    endpoint: "/api/v1/customers/search"
    parameters:
      query:
        type: string
        description: "Search query (name, email, or company)"
        required: true
        examples: ["John Doe", "john@example.com", "ACME Corp"]
      limit:
        type: integer
        description: "Maximum number of results"
        default: 20
        minimum: 1
        maximum: 100
    transform:
      engine: jq
      script: |
        .results[] | {
          id: .customer_id,
          name: .full_name,
          email: .email_address,
          company: .company_name,
          last_contact: .last_interaction_date
        }
    
  - name: create_opportunity
    type: execute
    description: "Create new sales opportunity"
    endpoint: "/api/v1/opportunities"
    method: POST
    parameters:
      customer_id:
        type: string
        description: "Customer ID"
        required: true
      title:
        type: string
        description: "Opportunity title"
        required: true
      value:
        type: number
        description: "Opportunity value in USD"
        required: true
        minimum: 0
      stage:
        type: string
        description: "Sales stage"
        default: "prospecting"
        enum: [prospecting, qualification, proposal, negotiation, closed_won, closed_lost]
    validation:
      - field: value
        rule: "value > 0"
        message: "Opportunity value must be positive"
        
prompts:
  - name: sales_assistant
    description: "AI assistant for sales team"
    content: |
      You are an expert sales assistant with access to our CRM system.
      
      Key responsibilities:
      - Help find and qualify potential customers
      - Create and track sales opportunities
      - Provide insights on customer interactions
      
      Guidelines:
      - Always confirm before creating opportunities >$50,000
      - Use customer's preferred communication method
      - Update opportunity stages based on interactions
      
    suggested_tools: [search_customers, create_opportunity]
    context:
      role: sales_assistant
      department: sales
      access_level: standard
```

## Tool Types and Patterns

### 1. List Tools
Retrieve collections of items:
```yaml
- name: list_products
  type: list  
  description: "List all products"
  endpoint: "/products"
  parameters:
    category:
      type: string
      description: "Filter by category"
    active_only:
      type: boolean  
      default: true
```

### 2. Details Tools
Get specific item information:
```yaml
- name: get_customer
  type: details
  description: "Get customer details by ID"
  endpoint: "/customers/{customer_id}"
  parameters:
    customer_id:
      type: string
      required: true
      path_parameter: true
```

### 3. Search Tools
Find items by query:
```yaml
- name: search_orders
  type: search
  description: "Search orders by various criteria"
  endpoint: "/orders/search"
  parameters:
    query:
      type: string
      required: true
    date_from:
      type: string
      format: date
    status:
      type: string
      enum: [pending, shipped, delivered, cancelled]
```

### 4. Execute Tools  
Perform actions or create items:
```yaml
- name: create_customer
  type: execute
  description: "Create new customer"
  endpoint: "/customers"
  method: POST
  parameters:
    name:
      type: string
      required: true
    email:
      type: string
      format: email
      required: true
    phone:
      type: string
      format: phone
```

### 5. Query Tools (Database)
Execute SQL queries:
```yaml
- name: revenue_report  
  type: query
  description: "Generate revenue report for date range"
  sql: |
    SELECT 
      DATE_TRUNC('month', order_date) as month,
      SUM(total_amount) as revenue,
      COUNT(*) as order_count
    FROM orders 
    WHERE order_date BETWEEN {start_date} AND {end_date}
      AND status = 'completed'
    GROUP BY month
    ORDER BY month DESC
  parameters:
    start_date:
      type: string
      format: date
      required: true
    end_date:
      type: string
      format: date
      required: true
```

## Authentication Methods

### 1. Bearer Token
```yaml
auth:
  method: bearer
  token: "${API_TOKEN}"
```

### 2. Basic Authentication
```yaml
auth:
  method: basic
  username: "${API_USERNAME}"  
  password: "${API_PASSWORD}"
```

### 3. API Key
```yaml
auth:
  method: api_key
  key: "${API_KEY}"
  location: header  # or query
  parameter: "X-API-Key"
```

### 4. OAuth2
```yaml
auth:
  method: oauth2
  config:
    client_id: "${OAUTH_CLIENT_ID}"
    client_secret: "${OAUTH_CLIENT_SECRET}"
    token_url: "https://api.example.com/oauth/token"
    scopes: [read, write]
    grant_type: client_credentials
```

## Response Transformation

### Using jq (JSON processor)
```yaml
transform:
  engine: jq
  script: |
    .data[] | {
      id: .customer_id,
      name: "\(.first_name) \(.last_name)",
      email: .contact.email,
      total_orders: .statistics.order_count
    }
```

### Using JavaScript
```yaml
transform:
  engine: javascript
  script: |
    function transform(response) {
      return response.data.map(customer => ({
        id: customer.customer_id,
        name: `${customer.first_name} ${customer.last_name}`,
        email: customer.contact.email,
        total_orders: customer.statistics.order_count
      }));
    }
```

### Using Python
```yaml
transform:
  engine: python
  script: |
    def transform(response):
      results = []
      for customer in response['data']:
        results.append({
          'id': customer['customer_id'],
          'name': f"{customer['first_name']} {customer['last_name']}",
          'email': customer['contact']['email'],
          'total_orders': customer['statistics']['order_count']
        })
      return results
```

## Error Handling and Validation

### Input Validation
```yaml
parameters:
  email:
    type: string
    format: email
    required: true
  age:
    type: integer
    minimum: 18
    maximum: 120
  country:
    type: string
    enum: [US, CA, UK, DE, FR, AU]
    
validation:
  - field: email
    rule: "contains(@, '.')"
    message: "Valid email address required"
  - field: age  
    rule: "age >= 21 if country == 'US'"
    message: "Must be 21+ for US customers"
```

### Error Response Handling
```yaml
error_handling:
  - status_code: 400
    message: "Invalid request parameters"
    retry: false
  - status_code: 429  
    message: "Rate limit exceeded"
    retry: true
    delay: 60
  - status_code: [500, 502, 503]
    message: "Server error - retrying"
    retry: true
    max_retries: 3
```

## Testing and Development

### 1. Validate Pack Structure
```bash
# Validate pack configuration
catalyst-packs validate my-pack/

# Detailed validation with warnings
catalyst-packs validate my-pack/ --verbose --warnings
```

### 2. Test Individual Tools
```bash
# Test specific tool
catalyst-packs test my-pack search_customers --query "John Doe"

# Test with different parameters  
catalyst-packs test my-pack create_opportunity \
  --customer_id "12345" \
  --title "New Enterprise Deal" \
  --value 50000
```

### 3. Dry Run Mode
```bash
# Test without making actual API calls
catalyst-packs install my-pack/ --dry-run

# Show what would be deployed
catalyst-packs deploy my-pack/ --dry-run --verbose
```

## Deployment and Management

### 1. Install Pack Locally
```bash
# Install for development
catalyst-packs install my-pack/ --mode development

# Install for production  
catalyst-packs install my-pack/ --mode production
```

### 2. Pack Versioning
```bash
# Update version in pack.yaml, then:
catalyst-packs publish my-pack/

# Tag release
git tag v1.2.0
git push origin v1.2.0
```

### 3. Environment Management
```bash
# Development environment
catalyst-packs install my-pack/ --env development

# Staging environment
catalyst-packs install my-pack/ --env staging --validate-endpoints

# Production environment  
catalyst-packs install my-pack/ --env production --backup --health-check
```

## Advanced Features

### Dynamic Parameter Resolution
```yaml
parameters:
  region:
    type: string
    resolver: environment
    env_var: DEFAULT_REGION
  user_id:
    type: string  
    resolver: context
    context_key: current_user_id
```

### Conditional Tool Execution
```yaml
tools:
  - name: admin_only_action
    type: execute
    description: "Administrative action"
    conditions:
      - user.role == "admin"
      - environment != "production" or approval.granted == true
```

### Custom Hooks
```yaml
hooks:
  before_request:
    - validate_rate_limit
    - log_request
  after_response:  
    - cache_response
    - update_metrics
  on_error:
    - log_error
    - send_alert
```

## Best Practices

### Security
- Store all credentials in environment variables
- Use least-privilege authentication scopes
- Implement proper input validation and sanitization
- Enable audit logging for sensitive operations
- Regularly rotate API keys and tokens

### Performance
- Implement response caching for frequently accessed data
- Use pagination for large result sets
- Set appropriate request timeouts
- Monitor and respect API rate limits
- Optimize database queries with proper indexing

### Maintainability
- Use semantic versioning (major.minor.patch)
- Maintain comprehensive documentation
- Include usage examples and test cases
- Follow consistent naming conventions
- Implement proper error messages and logging

### User Experience
- Provide clear, descriptive tool names and descriptions
- Include parameter examples and validation
- Design intuitive AI prompts and workflows
- Test with real business scenarios
- Gather feedback from actual users

---

**Next Steps**: 
- Explore [Integration Patterns](INTEGRATION_PATTERNS.md) for common scenarios
- Review [Security Guide](SECURITY.md) for authentication best practices
- Check [CLI Reference](CLI_REFERENCE.md) for complete command documentation