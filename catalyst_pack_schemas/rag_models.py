"""RAG (Retrieval Augmented Generation) models for Catalyst knowledge packs.

This module provides data models for configuring RAG capabilities with vector databases,
specifically optimized for Qdrant with ColPali multi-modal support.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Literal, Optional


class RAGProvider(Enum):
    """Supported RAG/Vector database providers."""
    
    QDRANT = "qdrant"
    # Future providers can be added here:
    # PINECONE = "pinecone"
    # WEAVIATE = "weaviate"
    # CHROMA = "chroma"


class VectorDistanceMetric(Enum):
    """Vector similarity distance metrics."""
    
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"


@dataclass
class QdrantConfig:
    """Qdrant-specific configuration for RAG."""
    
    # Connection settings
    qdrant_url: str = field(
        default="http://localhost:6333",
        metadata={"description": "Qdrant server URL"}
    )
    qdrant_api_key: Optional[str] = field(
        default=None,
        metadata={"description": "Qdrant API key for authentication"}
    )
    collection_name: str = field(
        default="documents",
        metadata={"description": "Qdrant collection name for storing vectors"}
    )
    
    # ColPali model settings
    colpali_model: str = field(
        default="vidore/colpali-v1.2",
        metadata={"description": "ColPali model for visual document processing"}
    )
    colpali_device: str = field(
        default="cuda",
        metadata={"description": "Device for ColPali model (cuda/cpu)"}
    )
    
    # Performance optimization
    enable_quantization: bool = field(
        default=True,
        metadata={"description": "Enable binary quantization for 90% storage reduction"}
    )
    enable_two_stage_retrieval: bool = field(
        default=True,
        metadata={"description": "Enable Qdrant's 13x performance optimization"}
    )
    
    # Vector settings
    vector_size: int = field(
        default=128,
        metadata={"description": "Vector dimension size"}
    )
    distance_metric: VectorDistanceMetric = field(
        default=VectorDistanceMetric.COSINE,
        metadata={"description": "Vector similarity metric"}
    )
    
    # Processing settings
    batch_size: int = field(
        default=32,
        metadata={"description": "Batch size for document processing"}
    )
    max_retries: int = field(
        default=3,
        metadata={"description": "Maximum retry attempts for API calls"}
    )
    timeout_seconds: int = field(
        default=60,
        metadata={"description": "Request timeout in seconds"}
    )
    
    # Storage optimization
    on_disk_payload: bool = field(
        default=False,
        metadata={"description": "Store payload on disk to save RAM"}
    )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "qdrant_url": self.qdrant_url,
            "qdrant_api_key": self.qdrant_api_key,
            "collection_name": self.collection_name,
            "colpali_model": self.colpali_model,
            "colpali_device": self.colpali_device,
            "enable_quantization": self.enable_quantization,
            "enable_two_stage_retrieval": self.enable_two_stage_retrieval,
            "vector_size": self.vector_size,
            "distance_metric": self.distance_metric.value,
            "batch_size": self.batch_size,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "on_disk_payload": self.on_disk_payload,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "QdrantConfig":
        """Create from dictionary."""
        if "distance_metric" in data and isinstance(data["distance_metric"], str):
            data["distance_metric"] = VectorDistanceMetric(data["distance_metric"])
        return cls(**data)


@dataclass
class RAGConfiguration:
    """RAG configuration for Catalyst knowledge packs.
    
    This configuration enables visual document search and retrieval
    using multi-modal embeddings and vector databases.
    """
    
    # Basic settings
    enabled: bool = field(
        default=False,
        metadata={"description": "Enable RAG functionality for this pack"}
    )
    provider: RAGProvider = field(
        default=RAGProvider.QDRANT,
        metadata={"description": "RAG/Vector database provider"}
    )
    
    # Provider-specific configurations
    qdrant_config: Optional[QdrantConfig] = field(
        default=None,
        metadata={"description": "Qdrant-specific configuration"}
    )
    
    # Document processing
    supported_formats: List[str] = field(
        default_factory=lambda: ["pdf", "png", "jpg", "jpeg"],
        metadata={"description": "Supported document formats for indexing"}
    )
    auto_index: bool = field(
        default=False,
        metadata={"description": "Automatically index new documents"}
    )
    chunk_size: int = field(
        default=1000,
        metadata={"description": "Document chunk size for text documents"}
    )
    chunk_overlap: int = field(
        default=200,
        metadata={"description": "Overlap between document chunks"}
    )
    
    # Search settings
    default_top_k: int = field(
        default=5,
        metadata={"description": "Default number of results to return"}
    )
    score_threshold: float = field(
        default=0.7,
        metadata={"description": "Minimum similarity score for results"}
    )
    
    # Cost management
    enable_cost_tracking: bool = field(
        default=True,
        metadata={"description": "Track RAG processing costs"}
    )
    monthly_budget_usd: Optional[float] = field(
        default=None,
        metadata={"description": "Monthly budget limit in USD"}
    )
    
    # Access control (simplified for MVP)
    access_level: Literal["global", "user", "organization"] = field(
        default="global",
        metadata={"description": "Document access level (global for MVP)"}
    )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for YAML serialization."""
        result = {
            "enabled": self.enabled,
            "provider": self.provider.value,
            "supported_formats": self.supported_formats,
            "auto_index": self.auto_index,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "default_top_k": self.default_top_k,
            "score_threshold": self.score_threshold,
            "enable_cost_tracking": self.enable_cost_tracking,
            "access_level": self.access_level,
        }
        
        if self.qdrant_config:
            result["qdrant_config"] = self.qdrant_config.to_dict()
        
        if self.monthly_budget_usd is not None:
            result["monthly_budget_usd"] = self.monthly_budget_usd
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RAGConfiguration":
        """Create from dictionary."""
        # Convert provider string to enum
        if "provider" in data and isinstance(data["provider"], str):
            data["provider"] = RAGProvider(data["provider"])
        
        # Parse Qdrant config if present
        if "qdrant_config" in data and data["qdrant_config"]:
            data["qdrant_config"] = QdrantConfig.from_dict(data["qdrant_config"])
        
        return cls(**data)


@dataclass
class RAGToolConfig:
    """Configuration for RAG-enabled tools."""
    
    rag_enabled: bool = field(
        default=False,
        metadata={"description": "Tool uses RAG for enhanced responses"}
    )
    search_scope: Literal["global", "user", "all"] = field(
        default="global",
        metadata={"description": "Search scope for RAG queries"}
    )
    include_metadata: bool = field(
        default=True,
        metadata={"description": "Include document metadata in results"}
    )
    max_results: int = field(
        default=5,
        metadata={"description": "Maximum results to return"}
    )


# Convenience function for creating default RAG config
def create_default_rag_config() -> RAGConfiguration:
    """Create a default RAG configuration with Qdrant."""
    return RAGConfiguration(
        enabled=True,
        provider=RAGProvider.QDRANT,
        qdrant_config=QdrantConfig(),
        enable_cost_tracking=True,
        access_level="global"  # MVP: all documents are global
    )