"""
Lineage Routes
"""
import logging
from typing import Dict, Any, Tuple, List

from api.database import get_db
from src.url_parser import URLParser

logger = logging.getLogger(__name__)


def get_artifact_lineage(artifact_id: str) -> Tuple[int, Any]:
    """
    Get lineage graph for a model artifact
    Returns: (status_code, response_body)
    """
    db = get_db()
    
    # Check artifact exists
    artifact = db.get_artifact("model", artifact_id)
    if not artifact:
        return 404, {"error": "Artifact not found"}
    
    name = artifact.get("name", "")
    url = artifact.get("url", "")
    
    # Start with the artifact itself
    nodes = [
        {
            "artifact_id": artifact_id,
            "name": name,
            "source": "registry",
            "metadata": {
                "url": url,
                "type": "model"
            }
        }
    ]
    edges = []
    
    # Get stored lineage
    lineage = artifact.get("lineage", [])
    
    # If no stored lineage, try to extract from URL
    if not lineage and url:
        lineage = _extract_lineage_from_url(url)
    
    # Add lineage nodes and edges
    for parent_name in lineage:
        parent_id = str(abs(hash(parent_name)) % 10_000_000_000)
        
        # Determine relationship type
        relationship = _determine_relationship(parent_name)
        
        nodes.append({
            "artifact_id": parent_id,
            "name": parent_name,
            "source": "config_json",
            "metadata": {}
        })
        
        edges.append({
            "from_node_artifact_id": parent_id,
            "to_node_artifact_id": artifact_id,
            "relationship": relationship
        })
    
    return 200, {
        "nodes": nodes,
        "edges": edges
    }


def _extract_lineage_from_url(url: str) -> List[str]:
    """Extract lineage by fetching model metadata"""
    lineage = []
    
    try:
        parser = URLParser()
        model_info = parser.parse_model_url(url)
        
        if not model_info:
            return lineage
        
        api_data = model_info.api_data or {}
        
        # Check cardData
        card_data = api_data.get("cardData", {})
        if isinstance(card_data, dict):
            # Base model
            base_model = card_data.get("base_model")
            if base_model:
                if isinstance(base_model, list):
                    lineage.extend(base_model)
                else:
                    lineage.append(base_model)
            
            # Training datasets
            datasets = card_data.get("datasets", [])
            if isinstance(datasets, list):
                lineage.extend(datasets[:3])
        
        # Check config for _name_or_path
        config = api_data.get("config", {})
        if isinstance(config, dict):
            name_or_path = config.get("_name_or_path", "")
            if name_or_path and name_or_path not in lineage:
                lineage.append(name_or_path)
        
        # Check tags
        for tag in model_info.tags:
            if tag.startswith("base_model:"):
                bm = tag.split(":", 1)[1]
                if bm not in lineage:
                    lineage.append(bm)
            elif tag.startswith("dataset:"):
                ds = tag.split(":", 1)[1]
                if ds not in lineage:
                    lineage.append(ds)
    
    except Exception as e:
        logger.warning(f"Error extracting lineage: {e}")
    
    return list(set(lineage))[:10]  # Dedupe and limit


def _determine_relationship(parent_name: str) -> str:
    """Determine the type of relationship based on parent name"""
    name_lower = parent_name.lower()
    
    # Dataset indicators
    dataset_keywords = ["squad", "glue", "imagenet", "coco", "wikipedia", 
                       "bookcorpus", "c4", "pile", "openwebtext", "dataset"]
    if any(kw in name_lower for kw in dataset_keywords):
        return "training_dataset"
    
    # Model indicators (default)
    return "base_model"
