# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-01-11

### Added
- **LLM Optimization Support** - New optional `llm_metadata` field for tools
  - `display_name` - Human-friendly names with emoji support
  - `usage_hint` - Guidance on when to use the tool
  - `complexity` - Tool complexity levels (basic/intermediate/advanced)
  - `prerequisites` - Tools that should be used first
  - `examples` - Usage scenarios and examples

- **Parameter Constraints** - New optional `constraints` field for parameters
  - `min`/`max` - Numeric value bounds
  - `min_length`/`max_length` - String length limits
  - `pattern` - Regex validation patterns
  - `examples` - Example values for LLM guidance

- **Backward Compatibility Tests** - Comprehensive test suite to ensure existing packs continue to work

### Changed
- **Documentation Improvements**
  - Added descriptions to `transform.file` and `transform.function` fields
  - Added descriptions to `form_data` and `query_params` fields
  - Clarified all transform type descriptions

### Technical Details
- All new fields are optional to maintain 100% backward compatibility
- Existing packs continue to work without any modifications
- Schema version remains compatible with v1.0.x

## [1.0.0] - Previous Release
- Initial release of Catalyst Builder