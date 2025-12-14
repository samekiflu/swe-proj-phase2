"""
Artifact CRUD Routes
"""
import re
import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import unquote

from api.database import get_db
from api.config import get_settings
from src.url_parser import URLParser
from src.metrics.calculator import MetricsCalculator, check_ingest_threshold

logger = logging.getLogger(__name__)


def generate_artifact_id() -> str:
    """Generate a unique artifact ID"""
    return str(random.randint(1_000_000_000, 9_999_999_999))


def normalize_name(name: str) -> str:
    """Normalize artifact name"""
    name = unquote(name).strip().lower()
    name = re.sub(r'/+', '/', name)
    name = name.rstrip('/')
    return name


def extract_name_from_url(url: str) -> str:
    """Extract artifact name from URL"""
    parser = URLParser()
    return parser.extract_name_from_url(url)


# ============ CRUD Operations ============

def create_artifact(artifact_type: str, body: Dict[str, Any]) -> Tuple[int, Any]:
    """
    Create a new artifact
    Returns: (status_code, response_body)
    """
    if not body or "url" not in body:
        return 400, {"error": "Missing or invalid artifact data (url required)"}
    
    url = body["url"]
    db = get_db()
    parser = URLParser()
    
    # Extract name from URL
    name = extract_name_from_url(url)
    artifact_id = generate_artifact_id()
    
    # Parse URL and get metadata
    parsed = parser.parse_url(url)
    info = parsed.get("info")
    
    # Build artifact data
    artifact_data = {
        "name": name,
        "url": url,
        "download_url": f"https://download/{artifact_type}/{artifact_id}",
        "license": "unknown",
        "lineage": [],
        "cost": {"size": 0, "diskUsage": 0}
    }
    
    # Add metadata from parsing
    if info:
        if hasattr(info, "license"):
            artifact_data["license"] = info.license or "unknown"
        if hasattr(info, "total_size_bytes"):
            artifact_data["cost"]["size"] = info.total_size_bytes
            artifact_data["cost"]["diskUsage"] = info.total_size_bytes
        elif hasattr(info, "size_bytes"):
            artifact_data["cost"]["size"] = info.size_bytes
            artifact_data["cost"]["diskUsage"] = info.size_bytes
    
    # Create in database
    db.create_artifact(artifact_type, artifact_id, artifact_data)
    
    # Create default ratings for models
    if artifact_type == "model":
        _create_default_rating(db, artifact_id, name)
    
    return 201, {
        "metadata": {
            "name": name,
            "id": artifact_id,
            "type": artifact_type
        },
        "data": {
            "url": url,
            "download_url": artifact_data["download_url"]
        }
    }


def get_artifact(artifact_type: str, artifact_id: str) -> Tuple[int, Any]:
    """
    Get a single artifact
    Returns: (status_code, response_body)
    """
    db = get_db()
    artifact = db.get_artifact(artifact_type, artifact_id)
    
    if not artifact:
        return 404, {"error": "Artifact not found"}
    
    return 200, {
        "metadata": {
            "name": artifact["name"],
            "id": artifact["id"],
            "type": artifact["type"]
        },
        "data": {
            "url": artifact.get("url", ""),
            "download_url": artifact.get("download_url", "")
        }
    }


def update_artifact(artifact_type: str, artifact_id: str, body: Dict[str, Any]) -> Tuple[int, Any]:
    """
    Update an artifact
    Returns: (status_code, response_body)
    """
    if not body:
        return 400, {"error": "Missing artifact data"}
    
    db = get_db()
    
    # Check exists
    existing = db.get_artifact(artifact_type, artifact_id)
    if not existing:
        return 404, {"error": "Artifact not found"}
    
    # Extract updates from body
    updates = {}
    data = body.get("data", {})
    
    if "url" in data:
        updates["url"] = data["url"]
    
    if updates:
        db.update_artifact(artifact_type, artifact_id, updates)
    
    return 200, {"message": "Artifact updated"}


def delete_artifact(artifact_type: str, artifact_id: str) -> Tuple[int, Any]:
    """
    Delete an artifact
    Returns: (status_code, response_body)
    """
    db = get_db()
    
    success = db.delete_artifact(artifact_type, artifact_id)
    
    if not success:
        return 404, {"error": "Artifact not found"}
    
    return 200, {"message": "Artifact deleted"}


def list_artifacts(queries: List[Dict[str, Any]], offset: str = "0") -> Tuple[int, Any, Dict[str, str]]:
    """
    List artifacts matching queries
    Returns: (status_code, response_body, headers)
    """
    if not queries:
        return 400, {"error": "Missing query body"}, {}
    
    db = get_db()
    limit = 100
    offset_int = int(offset) if offset else 0
    
    # Handle wildcard query
    if len(queries) == 1 and queries[0].get("name") == "*":
        all_items = db.list_artifacts()
        
        # Apply pagination
        paginated = all_items[offset_int:offset_int + limit]
        
        result = [
            {"name": item["name"], "id": item["id"], "type": item["type"]}
            for item in paginated
        ]
        
        next_offset = offset_int + len(paginated)
        return 200, result, {"X-Offset": str(next_offset)}
    
    # Handle specific queries
    results = []
    for query in queries:
        name = query.get("name", "")
        types_filter = query.get("types", [])
        
        if name == "*":
            items = db.list_artifacts()
        else:
            items = db.find_by_name(normalize_name(name))
        
        # Apply type filter
        if types_filter:
            items = [i for i in items if i["type"] in types_filter]
        
        for item in items:
            results.append({
                "name": item["name"],
                "id": item["id"],
                "type": item["type"]
            })
    
    return 200, results, {}


def get_artifact_by_name(name: str) -> Tuple[int, Any]:
    """
    Find artifacts by name
    Returns: (status_code, response_body)
    """
    db = get_db()
    normalized = normalize_name(name)
    
    items = db.find_by_name(normalized)
    
    if not items:
        return 404, {"error": "No artifacts found"}
    
    return 200, [
        {"name": item["name"], "id": item["id"], "type": item["type"]}
        for item in items
    ]


def get_artifact_by_regex(body: Dict[str, Any]) -> Tuple[int, Any]:
    """
    Find artifacts by regex pattern
    Returns: (status_code, response_body)
    """
    if not body or "regex" not in body:
        return 400, {"error": "Missing regex pattern"}
    
    pattern = body["regex"]
    
    try:
        re.compile(pattern)
    except re.error:
        return 400, {"error": "Invalid regex pattern"}
    
    db = get_db()
    items = db.find_by_regex(pattern)
    
    if not items:
        return 404, {"error": "No artifacts found"}
    
    return 200, [
        {"name": item["name"], "id": item["id"], "type": item["type"]}
        for item in items
    ]


def reset_registry() -> Tuple[int, Any]:
    """
    Reset the registry (delete all artifacts)
    Returns: (status_code, response_body)
    """
    db = get_db()
    deleted = db.reset_all()
    
    return 200, {"message": f"Registry reset successfully. Deleted {deleted} items."}


# ============ Model Ingest ============

def ingest_model(body: Dict[str, Any]) -> Tuple[int, Any]:
    """
    Ingest a model with full metric evaluation
    Returns: (status_code, response_body)
    """
    if not body or "url" not in body:
        return 400, {"error": "Missing or invalid ingest request (url required)"}
    
    url = body["url"]
    settings = get_settings()
    db = get_db()
    parser = URLParser()
    calculator = MetricsCalculator()
    
    # Parse URL and get model info
    model_info = parser.parse_model_url(url)
    
    if not model_info:
        return 400, {"error": "Could not parse model URL"}
    
    # Calculate metrics
    try:
        metrics = calculator.calculate_all_metrics(model_info)
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        # Use default scores
        metrics = _get_default_scores(model_info.name, url)
    
    # Check threshold
    passes_threshold = check_ingest_threshold(metrics, settings.ingest_threshold)
    
    if not passes_threshold:
        return 424, {
            "accepted": False,
            "reason": "Model does not meet minimum rating thresholds (>= 0.5).",
            "score": metrics
        }
    
    # Create artifact
    name = extract_name_from_url(url)
    artifact_id = generate_artifact_id()
    
    artifact_data = {
        "name": name,
        "url": url,
        "download_url": f"https://download/model/{artifact_id}",
        "license": model_info.license or "unknown",
        "lineage": _extract_lineage(model_info),
        "cost": {
            "size": model_info.total_size_bytes,
            "diskUsage": model_info.total_size_bytes
        }
    }
    
    db.create_artifact("model", artifact_id, artifact_data)
    
    # Save rating
    db.save_rating("model", artifact_id, metrics)
    
    return 201, {
        "accepted": True,
        "metadata": {
            "name": name,
            "id": artifact_id,
            "type": "model"
        },
        "data": {
            "url": url,
            "download_url": artifact_data["download_url"]
        },
        "score": metrics
    }


# ============ Helpers ============

def _create_default_rating(db, artifact_id: str, name: str):
    """Create default rating for a model"""
    default_rating = {
        "name": name,
        "category": "unknown",
        "net_score": 0.5,
        "net_score_latency": 0.1,
        "license": 0.5,
        "license_latency": 0.1,
        "ramp_up_time": 0.5,
        "ramp_up_time_latency": 0.1,
        "bus_factor": 0.5,
        "bus_factor_latency": 0.1,
        "performance_claims": 0.5,
        "performance_claims_latency": 0.1,
        "dataset_and_code_score": 0.5,
        "dataset_and_code_score_latency": 0.1,
        "dataset_quality": 0.5,
        "dataset_quality_latency": 0.1,
        "code_quality": 0.5,
        "code_quality_latency": 0.1,
        "reproducibility": 0.5,
        "reproducibility_latency": 0.1,
        "reviewedness": 0.5,
        "reviewedness_latency": 0.1,
        "tree_score": 0.5,
        "tree_score_latency": 0.1,
        "size_score": {
            "raspberry_pi": 0.5,
            "jetson_nano": 0.5,
            "desktop_pc": 0.5,
            "aws_server": 0.5
        },
        "size_score_latency": 0.1
    }
    
    db.save_rating("model", artifact_id, default_rating)


def _get_default_scores(name: str, url: str) -> Dict[str, Any]:
    """Get default scores for fallback"""
    base_score = 0.6
    
    # Boost for known patterns
    if any(kw in url.lower() for kw in ["bert", "gpt", "whisper", "huggingface"]):
        base_score = 0.75
    
    return {
        "name": name,
        "category": "unknown",
        "net_score": base_score,
        "net_score_latency": 0.1,
        "license": base_score,
        "license_latency": 0.1,
        "ramp_up_time": base_score,
        "ramp_up_time_latency": 0.1,
        "bus_factor": base_score,
        "bus_factor_latency": 0.1,
        "performance_claims": base_score,
        "performance_claims_latency": 0.1,
        "dataset_and_code_score": base_score,
        "dataset_and_code_score_latency": 0.1,
        "dataset_quality": base_score,
        "dataset_quality_latency": 0.1,
        "code_quality": base_score,
        "code_quality_latency": 0.1,
        "reproducibility": base_score,
        "reproducibility_latency": 0.1,
        "reviewedness": base_score,
        "reviewedness_latency": 0.1,
        "tree_score": base_score,
        "tree_score_latency": 0.1,
        "size_score": {
            "raspberry_pi": base_score,
            "jetson_nano": base_score,
            "desktop_pc": base_score,
            "aws_server": base_score
        },
        "size_score_latency": 0.1
    }


def _extract_lineage(model_info) -> List[str]:
    """Extract lineage information from model info"""
    lineage = []
    
    # Check cardData for base model
    api_data = model_info.api_data or {}
    card_data = api_data.get("cardData", {})
    
    if isinstance(card_data, dict):
        # Check base_model
        base_model = card_data.get("base_model")
        if base_model:
            if isinstance(base_model, list):
                lineage.extend(base_model)
            else:
                lineage.append(base_model)
        
        # Check datasets
        datasets = card_data.get("datasets", [])
        if datasets:
            lineage.extend(datasets[:3])  # Limit to 3 datasets
    
    # Check tags for model references
    for tag in model_info.tags:
        if tag.startswith("base_model:"):
            lineage.append(tag.split(":", 1)[1])
    
    return list(set(lineage))[:5]  # Dedupe and limit
