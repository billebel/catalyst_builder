# Pack Security Guardrails Guide

## Overview

Catalyst packs can include a `guardrails.yaml` file that defines security patterns and operational boundaries.

Each pack can include a `guardrails.yaml` file that defines:
- **Blocked patterns** - Operations that are completely prohibited
- **Warning patterns** - Operations that generate alerts but are allowed  
- **Auto-modifications** - Automatic request/response transformations
- **Compliance frameworks** - SOX, GDPR, HIPAA rule enforcement
- **Environment-specific overrides** - Different rules for dev/staging/production

## Quick Start

Create a `guardrails.yaml` file in your pack directory:

```yaml
# pack-name/guardrails.yaml
metadata:
  name: "my_pack_guardrails" 
  version: "1.0.0"
  description: "Security controls for MyPack"

# Block dangerous operations
blocked_patterns:
  write_operations:
    enabled: true
    patterns:
      - "INSERT\\s+INTO"
      - "UPDATE\\s+.*SET" 
      - "DELETE\\s+FROM"
    message: "Write operations blocked for read-only pack"
    severity: "critical"

# Warn about performance issues    
warning_patterns:
  large_queries:
    enabled: true
    patterns:
      - "SELECT\\s+\\*\\s+FROM"
      - "LIMIT\\s+[5-9][0-9]{4,}"
    message: "Query may have performance impact"
    severity: "medium"

# Apply automatic enhancements
auto_modifications:
  add_timeouts:
    enabled: true
    type: "execution_parameter"
    conditions: ["always"]
    parameter: "timeout"
    value: "300"
    message: "Applied standard timeout"
```

The MCP platform will automatically:
1. Load your guardrails during pack registration
2. Apply rules to all pack tools automatically  
3. Block/warn/modify requests as configured
4. Generate compliance audit logs

## Pattern Matching

### Blocked Patterns

Operations that should never be allowed:

```yaml
blocked_patterns:
  # Database write operations
  dangerous_sql:
    enabled: true
    patterns:
      - "DROP\\s+(TABLE|DATABASE|SCHEMA)"
      - "TRUNCATE\\s+TABLE" 
      - "DELETE\\s+FROM\\s+\\w+\\s*($|;)"  # DELETE without WHERE
    message: "Destructive SQL operations are prohibited"
    recommendation: "Use SELECT queries for data analysis only"
    severity: "critical"
    
  # API write endpoints  
  write_endpoints:
    enabled: true
    patterns:
      - "/api/.*\\s+(POST|PUT|DELETE|PATCH)"
    message: "Write API operations blocked - read-only pack"
    severity: "critical"
    
  # Sensitive system access
  system_commands:
    enabled: true  
    patterns:
      - "\\|\\s*sh\\s+"           # Shell execution
      - "\\|\\s*eval\\s+"         # Code evaluation
      - "system\\("               # System function calls
    message: "System-level operations are prohibited for security"
    severity: "critical"
```

### Warning Patterns

Operations that are allowed but concerning:

```yaml
warning_patterns:
  # Performance concerns
  performance_issues:
    enabled: true
    patterns:
      - "SELECT\\s+.*\\s+FROM\\s+.*\\s+WHERE\\s+.*LIKE\\s+'%.*%'"  # Leading wildcards
      - ".*\\s+ORDER\\s+BY.*LIMIT\\s+[1-4][0-9]{4,}"              # Large result sets
    message: "Query may have significant performance impact"
    recommendation: "Consider adding indexes or reducing result set size" 
    severity: "medium"
    performance_impact: "May cause slower response times"
    
  # Compliance sensitive data
  sensitive_data_access:
    enabled: true
    patterns:
      - "SELECT\\s+.*\\s+(SSN|Social|CreditCard|BankAccount).*FROM"
      - "SELECT\\s+.*\\s+FROM\\s+(Users|Customers|Patients).*"
    message: "Query accesses potentially sensitive data - ensure compliance"
    recommendation: "Verify data access permissions and audit requirements"
    severity: "high"
    compliance_impact: "May require additional logging and access justification"
```

## Auto-Modifications

Automatically enhance requests for safety and performance:

```yaml
auto_modifications:
  # Add result limits
  result_limiting:
    enabled: true
    description: "Automatically add result limits to protect against large data sets"
    conditions:
      - "no_limit_specified"      # No LIMIT clause present
    modification:
      type: "append_clause"
      clause: "LIMIT {max_results_default}"
    message: "Added result limit for performance protection"
    
  # Timeout enforcement
  timeout_enforcement:
    enabled: true
    description: "Ensure all operations have appropriate timeouts"
    conditions:
      - "always"                  # Always apply
    modification:
      type: "execution_parameter"
      parameter: "timeout"
      value: "{timeout_seconds}"
    message: "Applied standard timeout for resource protection"
    
  # Field masking
  sensitive_field_masking:
    enabled: true
    description: "Automatically mask sensitive fields in responses"
    conditions:
      - "sensitive_field_detected"
    modification:
      type: "response_transformation"
      mask_patterns: ["SSN", "CreditCard", "Phone"]
      mask_character: "X"
    message: "Sensitive fields masked for privacy protection"
```

## Compliance Frameworks

### SOX Compliance (Financial)

```yaml
sox_compliance:
  # Critical change monitoring
  critical_changes:
    enabled: true
    monitor_objects: ["Account", "Opportunity", "Quote", "Order"]
    monitor_fields: ["Amount", "Probability", "CloseDate"]
    alert_threshold_minutes: 5
    require_justification: true
    audit_retention_days: 2555      # 7 years
    
  # Access control validation  
  access_controls:
    enabled: true
    validate_profile_changes: true
    prevent_weekend_changes: true   # Block weekend compliance changes
    require_dual_approval: true     # Two-person integrity
    
  # Financial data protection
  financial_controls:
    enabled: true
    encrypt_sensitive_fields: ["Amount", "Revenue", "Cost"]
    mask_financial_data: true       # Mask in logs
    restrict_bulk_financial_access: true
    audit_all_financial_queries: true
```

### Data Protection (GDPR/Privacy)

```yaml
data_protection:
  # PII detection and protection
  pii_controls:
    enabled: true
    detect_patterns:
      - "\\b\\d{3}-\\d{2}-\\d{4}\\b"                           # SSN
      - "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"  # Email
    mask_in_logs: true
    alert_on_detection: true
    require_encrypted_transport: true
    
  # Data export controls
  export_controls:
    enabled: true
    max_records_per_export: 10000
    require_approval_threshold: 1000
    block_sensitive_field_export: ["SSN", "CreditCard"]
    audit_all_exports: true
```

## Environment-Specific Configuration

Different rules for different environments:

```yaml
environments:
  development:
    # Relaxed limits for development
    limits:
      api_calls:
        daily_limit: 1000         # Lower limits in dev
        concurrent_limit: 5
    blocked_patterns:
      write_operations:
        enabled: false            # Allow writes in dev for testing
        
  staging:
    # Medium restrictions for staging
    limits:
      api_calls:
        daily_limit: 10000
        concurrent_limit: 10
    sox_compliance:
      critical_changes:
        alert_threshold_minutes: 15    # Less aggressive alerts
        
  production:
    # Strict controls in production
    limits:
      api_calls:
        daily_limit: 100000
        concurrent_limit: 25
    sox_compliance:
      critical_changes:
        enabled: true
        alert_threshold_minutes: 5    # Immediate alerts
```

## User/Role-Based Overrides

Different permissions for different user types:

```yaml
user_overrides:
  # Administrator roles
  admin_roles:
    - "System Administrator"
    - "Integration Admin"
  admin_limits:
    api_calls:
      daily_limit: 200000         # Higher limits for admins
      concurrent_limit: 50
    override_weekend_restrictions: true
    
  # Service accounts for automation
  service_account_roles:
    - "Service Account"
    - "ETL User"
  service_account_limits:
    api_calls:
      daily_limit: 150000
      concurrent_limit: 30        # Higher concurrency for automation
```

## Performance Scoring

Grade operations for optimization insights:

```yaml
performance_scoring:
  factors:
    index_usage:
      weight: 30
      description: "Efficient index usage improves performance"
    result_limiting:
      weight: 25  
      description: "Proper result limiting prevents timeouts"
    query_complexity:
      weight: 25
      description: "Simple queries execute faster"
    field_selection:
      weight: 20
      description: "Selecting specific fields reduces data transfer"
      
  grades:
    A: 90    # Excellent performance
    B: 75    # Good performance  
    C: 60    # Fair performance
    D: 40    # Poor performance
    F: 0     # Failed - blocked or error
```

## Advanced Features

### Machine Learning Anomaly Detection

```yaml
advanced_features:
  ml_anomaly_detection:
    enabled: true
    learning_period_days: 30
    anomaly_threshold: 0.95
    
  adaptive_limits:
    enabled: true
    adjustment_period_hours: 24
    max_adjustment_factor: 1.5
    
  predictive_compliance:
    enabled: true
    compliance_risk_modeling: true
    early_warning_system: true
```

### Emergency Override

```yaml
emergency_overrides:
  break_glass:
    enabled: true
    authorized_users: ["emergency_admin", "compliance_officer"]
    requires_justification: true
    auto_expire_minutes: 60
    audit_level: "maximum"
    
  disaster_recovery:
    enabled: true
    relaxed_limits_factor: 2.0    # Double limits during DR
    bypass_non_critical_warnings: true
```

## Integration with External Systems

```yaml
integrations:
  # SIEM integration
  siem_integration:
    enabled: true
    siem_endpoint: "${SIEM_WEBHOOK_URL}"
    api_key: "${SIEM_API_KEY}"
    event_types: ["security", "compliance", "audit"]
    
  # Compliance management tools
  compliance_tools:
    enabled: true
    grc_platform_url: "${GRC_PLATFORM_URL}"
    auto_create_incidents: true
```

## Best Practices

### Security-First Design
- **Default Deny**: Block operations by default, explicitly allow what's needed
- **Least Privilege**: Grant minimum necessary permissions
- **Defense in Depth**: Multiple layers of security controls

### Performance Optimization
- **Result Limiting**: Always limit result set sizes
- **Query Optimization**: Encourage efficient query patterns  
- **Timeout Enforcement**: Prevent runaway operations

### Compliance Automation
- **Audit Everything**: Log all operations for compliance
- **Data Classification**: Identify and protect sensitive data
- **Access Monitoring**: Track who accesses what when

### Testing Strategy
- **Test Blocked Operations**: Verify dangerous operations are blocked
- **Test Warning Generation**: Confirm alerts are generated appropriately
- **Test Auto-Modifications**: Validate automatic enhancements work
- **Test Environment Overrides**: Verify dev/staging/prod differences

## Example: Complete Enterprise Pack Guardrails

See `production/salesforce_enterprise/guardrails.yaml` for a comprehensive 455-line example implementing:
- Complete SOX compliance automation
- Enterprise API rate limiting
- Comprehensive pattern blocking (4 categories)
- Warning system (3 categories) 
- Auto-modifications (3 types)
- Environment-specific overrides
- User role-based permissions
- Audit trail integration

This transforms any pack into an enterprise-grade, compliance-ready solution with zero code changes required.