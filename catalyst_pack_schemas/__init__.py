"""Catalyst Pack Schemas - Complete toolkit for building and managing catalyst packs."""

from .builder import (
    PackBuilder,
    PackFactory,
    create_pack,
    quick_pack,
)
from .installer import (
    DeploymentOptions,
    DeploymentTarget,
    InstalledPack,
    MCPInstaller,
    PackInstaller,
    PackRegistry,
)
from .models import (  # Core Models; Configuration Classes; Enums; Exceptions
    AuthConfig,
    AuthMethod,
    ConnectionConfig,
    ExecutionStep,
    Pack,
    PackMetadata,
    PackValidationError,
    ParameterDefinition,
    PromptDefinition,
    ResourceDefinition,
    RetryPolicy,
    ToolDefinition,
    ToolType,
    TransformConfig,
    TransformEngine,
)
from .utils import (
    create_pack_index,
    discover_packs,
    export_pack_metadata,
    get_pack_statistics,
    load_pack_collection,
    validate_pack_structure,
)
from .validators import (
    PackCollectionValidator,
    PackValidator,
    validate_pack_dict,
    validate_pack_yaml,
)

__version__ = "1.0.0"
__all__ = [
    # Models
    "Pack",
    "PackMetadata",
    "ConnectionConfig",
    "ToolDefinition",
    "PromptDefinition",
    "ResourceDefinition",
    "AuthConfig",
    "RetryPolicy",
    "TransformConfig",
    "ExecutionStep",
    "ParameterDefinition",
    # Enums
    "ToolType",
    "AuthMethod",
    "TransformEngine",
    # Exceptions
    "PackValidationError",
    # Validators
    "PackValidator",
    "PackCollectionValidator",
    "validate_pack_yaml",
    "validate_pack_dict",
    # Builder
    "PackBuilder",
    "PackFactory",
    "quick_pack",
    "create_pack",
    # Installer
    "PackInstaller",
    "MCPInstaller",
    "InstalledPack",
    "PackRegistry",
    "DeploymentTarget",
    "DeploymentOptions",
    # Utils
    "discover_packs",
    "load_pack_collection",
    "get_pack_statistics",
    "create_pack_index",
    "export_pack_metadata",
    "validate_pack_structure",
]
