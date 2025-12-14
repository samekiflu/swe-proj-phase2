"""
Data classes for ML Model Evaluator & Registry
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ModelInfo:
    """Information about a HuggingFace model"""
    name: str              # "google/bert-base-uncased"
    url: str               # Full HuggingFace URL
    api_data: Dict         # Raw HF API response
    downloads: int = 0
    likes: int = 0
    last_modified: str = ""
    tags: List[str] = field(default_factory=list)
    pipeline_tag: str = ""  # "text-classification", etc.
    library_name: str = ""  # "transformers", "pytorch", etc.
    model_index: List[Dict] = field(default_factory=list)  # Benchmark results
    license: str = ""
    readme: str = ""
    siblings: List[Dict] = field(default_factory=list)  # File list
    
    @property
    def total_size_bytes(self) -> int:
        """Calculate total size from siblings (file list)"""
        total = 0
        for file_info in self.siblings:
            if isinstance(file_info, dict):
                total += file_info.get("size", 0)
        return total


@dataclass
class DatasetInfo:
    """Information about a HuggingFace dataset"""
    name: str
    url: str
    api_data: Dict
    downloads: int = 0
    likes: int = 0
    tags: List[str] = field(default_factory=list)
    license: str = ""
    readme: str = ""
    size_bytes: int = 0


@dataclass
class CodeInfo:
    """Information about a GitHub repository"""
    name: str              # "owner/repo"
    url: str
    api_data: Dict
    stars: int = 0
    forks: int = 0
    language: str = ""
    license: str = ""
    size_kb: int = 0       # GitHub returns size in KB
    open_issues: int = 0
    last_updated: str = ""
    readme: str = ""
    
    @property
    def size_bytes(self) -> int:
        return self.size_kb * 1024


@dataclass
class MetricResult:
    """Result from a single metric calculation"""
    name: str
    value: float           # 0.0 to 1.0
    latency_ms: int        # Calculation time in milliseconds
    details: Dict = field(default_factory=dict)  # Additional info


@dataclass
class SizeScore:
    """Hardware compatibility scores"""
    raspberry_pi: float = 0.0
    jetson_nano: float = 0.0
    desktop_pc: float = 0.0
    aws_server: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "raspberry_pi": self.raspberry_pi,
            "jetson_nano": self.jetson_nano,
            "desktop_pc": self.desktop_pc,
            "aws_server": self.aws_server
        }


@dataclass
class ModelRating:
    """Complete rating for a model"""
    name: str
    category: str
    net_score: float = 0.0
    net_score_latency: float = 0.0
    license: float = 0.0
    license_latency: float = 0.0
    ramp_up_time: float = 0.0
    ramp_up_time_latency: float = 0.0
    bus_factor: float = 0.0
    bus_factor_latency: float = 0.0
    performance_claims: float = 0.0
    performance_claims_latency: float = 0.0
    dataset_and_code_score: float = 0.0
    dataset_and_code_score_latency: float = 0.0
    dataset_quality: float = 0.0
    dataset_quality_latency: float = 0.0
    code_quality: float = 0.0
    code_quality_latency: float = 0.0
    reproducibility: float = 0.0
    reproducibility_latency: float = 0.0
    reviewedness: float = 0.0
    reviewedness_latency: float = 0.0
    tree_score: float = 0.0
    tree_score_latency: float = 0.0
    size_score: SizeScore = field(default_factory=SizeScore)
    size_score_latency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "net_score": self.net_score,
            "net_score_latency": self.net_score_latency,
            "license": self.license,
            "license_latency": self.license_latency,
            "ramp_up_time": self.ramp_up_time,
            "ramp_up_time_latency": self.ramp_up_time_latency,
            "bus_factor": self.bus_factor,
            "bus_factor_latency": self.bus_factor_latency,
            "performance_claims": self.performance_claims,
            "performance_claims_latency": self.performance_claims_latency,
            "dataset_and_code_score": self.dataset_and_code_score,
            "dataset_and_code_score_latency": self.dataset_and_code_score_latency,
            "dataset_quality": self.dataset_quality,
            "dataset_quality_latency": self.dataset_quality_latency,
            "code_quality": self.code_quality,
            "code_quality_latency": self.code_quality_latency,
            "reproducibility": self.reproducibility,
            "reproducibility_latency": self.reproducibility_latency,
            "reviewedness": self.reviewedness,
            "reviewedness_latency": self.reviewedness_latency,
            "tree_score": self.tree_score,
            "tree_score_latency": self.tree_score_latency,
            "size_score": self.size_score.to_dict(),
            "size_score_latency": self.size_score_latency
        }


@dataclass 
class LineageNode:
    """Node in a lineage graph"""
    artifact_id: str
    name: str
    source: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class LineageEdge:
    """Edge in a lineage graph"""
    from_node_artifact_id: str
    to_node_artifact_id: str
    relationship: str  # "base_model", "training_dataset", etc.


@dataclass
class LineageGraph:
    """Complete lineage graph for an artifact"""
    nodes: List[LineageNode] = field(default_factory=list)
    edges: List[LineageEdge] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "nodes": [
                {
                    "artifact_id": n.artifact_id,
                    "name": n.name,
                    "source": n.source,
                    "metadata": n.metadata
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "from_node_artifact_id": e.from_node_artifact_id,
                    "to_node_artifact_id": e.to_node_artifact_id,
                    "relationship": e.relationship
                }
                for e in self.edges
            ]
        }
