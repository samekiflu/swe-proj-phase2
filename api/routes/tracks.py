"""
Tracks Route
"""
from typing import Dict, Any, List

from api.database import get_db


def get_tracks() -> Dict[str, List[str]]:
    """
    Get planned tracks from database
    """
    db = get_db()
    
    try:
        config = db.get_config("TRACKS")
        if config:
            tracks = config.get("tracks", [])
            return {"plannedTracks": tracks}
    except Exception:
        pass
    
    # Return empty tracks by default
    return {"plannedTracks": []}
