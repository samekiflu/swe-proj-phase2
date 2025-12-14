"""
Cost Calculation Routes
"""
import logging
from typing import Dict, Any, Tuple

from api.database import get_db
from src.url_parser import URLParser

logger = logging.getLogger(__name__)

# Default cost in MB for unknown sizes
DEFAULT_COST_MB = 412.5


def get_artifact_cost(artifact_type: str, artifact_id: str, include_dependency: bool = False) -> Tuple[int, Any]:
    """
    Calculate artifact cost (download size in MB)
    Returns: (status_code, response_body)
    """
    db = get_db()
    
    # Check artifact exists
    artifact = db.get_artifact(artifact_type, artifact_id)
    if not artifact:
        return 404, {"error": "Artifact not found"}
    
    # Get cost from stored data or calculate
    cost_data = artifact.get("cost", {})
    size_bytes = cost_data.get("size", 0) or cost_data.get("diskUsage", 0)
    
    # Convert to MB
    if size_bytes > 0:
        standalone_cost = size_bytes / (1024 * 1024)
    else:
        # Try to fetch real size
        standalone_cost = _fetch_real_cost(artifact, artifact_type)
    
    if not include_dependency:
        return 200, {
            artifact_id: {
                "total_cost": round(standalone_cost, 2)
            }
        }
    
    # Include dependencies
    lineage = artifact.get("lineage", [])
    
    total_cost = standalone_cost
    result = {
        artifact_id: {
            "standalone_cost": round(standalone_cost, 2),
            "total_cost": round(standalone_cost, 2)  # Will be updated
        }
    }
    
    # Add dependency costs
    for dep_name in lineage[:5]:  # Limit to 5 dependencies
        dep_id = str(abs(hash(dep_name)) % 10_000_000_000)
        dep_cost = 280.0  # Default dependency cost
        
        result[dep_id] = {
            "standalone_cost": dep_cost,
            "total_cost": dep_cost
        }
        
        total_cost += dep_cost
    
    # Update main artifact's total cost
    result[artifact_id]["total_cost"] = round(total_cost, 2)
    
    return 200, result


def _fetch_real_cost(artifact: Dict[str, Any], artifact_type: str) -> float:
    """Fetch real cost from external APIs"""
    url = artifact.get("url", "")
    
    if not url:
        return DEFAULT_COST_MB
    
    try:
        import requests
        
        if "huggingface.co" in url and artifact_type in ("model", "dataset"):
            # Extract model/dataset ID
            parser = URLParser()
            
            if artifact_type == "model":
                model_id = parser._extract_model_id(url)
                api_url = f"https://huggingface.co/api/models/{model_id}"
            else:
                dataset_id = parser._extract_dataset_id(url)
                api_url = f"https://huggingface.co/api/datasets/{dataset_id}"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                siblings = data.get("siblings", [])
                total_bytes = sum(s.get("size", 0) for s in siblings if isinstance(s, dict))
                if total_bytes > 0:
                    return total_bytes / (1024 * 1024)
        
        elif "github.com" in url:
            # Extract owner/repo
            parser = URLParser()
            owner, repo = parser._extract_github_info(url)
            
            if owner and repo:
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    size_kb = data.get("size", 0)
                    if size_kb > 0:
                        return size_kb / 1024  # KB to MB
    
    except Exception as e:
        logger.warning(f"Error fetching real cost: {e}")
    
    return DEFAULT_COST_MB
