"""
License Check Routes
"""
import logging
from typing import Dict, Any, Tuple

from api.database import get_db
from src.url_parser import URLParser
from src.metrics.license_metric import LicenseMetric, check_license_compatibility

logger = logging.getLogger(__name__)


def check_license(artifact_id: str, body: Dict[str, Any]) -> Tuple[int, Any]:
    """
    Check license compatibility between model and GitHub repo
    Returns: (status_code, response_body)
    """
    if not body or "github_url" not in body:
        return 400, {"error": "Missing github_url in request body"}
    
    github_url = body["github_url"]
    db = get_db()
    
    # Check artifact exists
    artifact = db.get_artifact("model", artifact_id)
    if not artifact:
        return 404, {"error": "Artifact not found"}
    
    # Get artifact license
    artifact_license = artifact.get("license", "unknown")
    model_url = artifact.get("url", "")
    
    # If artifact license is unknown, try to fetch it
    if artifact_license == "unknown" and model_url:
        try:
            parser = URLParser()
            model_info = parser.parse_model_url(model_url)
            if model_info and model_info.license:
                artifact_license = model_info.license
        except Exception:
            pass
    
    # Fetch GitHub license
    github_license = "unknown"
    try:
        parser = URLParser()
        code_info = parser.parse_code_url(github_url)
        if code_info:
            github_license = code_info.license
    except Exception as e:
        logger.warning(f"Error fetching GitHub license: {e}")
        return 502, {"error": "Could not retrieve GitHub license information"}
    
    # Check compatibility
    compatible = check_license_compatibility(artifact_license, github_license)
    
    # Return boolean as per OpenAPI spec
    return 200, compatible
