"""
Rating Routes
"""
import logging
from typing import Dict, Any, Tuple

from api.database import get_db
from src.url_parser import URLParser
from src.metrics.calculator import MetricsCalculator

logger = logging.getLogger(__name__)


def rate_model(artifact_id: str) -> Tuple[int, Any]:
    """
    Get or calculate rating for a model
    Returns: (status_code, response_body)
    """
    db = get_db()
    
    # Check artifact exists
    artifact = db.get_artifact("model", artifact_id)
    if not artifact:
        return 404, {"error": "Artifact not found"}
    
    # Check for cached rating
    rating = db.get_latest_rating("model", artifact_id)
    
    if rating:
        # Return cached rating (remove internal fields)
        rating.pop("pk", None)
        rating.pop("sk", None)
        rating.pop("createdAt", None)
        return 200, rating
    
    # Calculate new rating
    url = artifact.get("url", "")
    if not url:
        return 500, {"error": "No URL for artifact, cannot calculate rating"}
    
    try:
        parser = URLParser()
        calculator = MetricsCalculator()
        
        model_info = parser.parse_model_url(url)
        if not model_info:
            return 500, {"error": "Could not parse model URL"}
        
        metrics = calculator.calculate_all_metrics(model_info)
        
        # Cache the rating
        db.save_rating("model", artifact_id, metrics)
        
        return 200, metrics
        
    except Exception as e:
        logger.error(f"Error calculating rating for {artifact_id}: {e}")
        return 500, {"error": f"Error calculating rating: {str(e)}"}
