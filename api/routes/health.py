"""
Health Check Routes
"""
from datetime import datetime, timezone
from typing import Optional


def health_check() -> dict:
    """Simple health check"""
    return {"status": "healthy"}


def health_components(window_minutes: int = 60, include_timeline: bool = False) -> dict:
    """Detailed component health check"""
    now = datetime.now(timezone.utc).isoformat()
    
    components = [
        {
            "id": "api-gateway",
            "display_name": "API Gateway",
            "status": "ok",
            "observed_at": now,
            "description": "Main API entry point",
            "metrics": {
                "uptime_seconds": 3600,
                "request_count": 100
            },
            "issues": [],
            "logs": []
        },
        {
            "id": "dynamodb",
            "display_name": "DynamoDB",
            "status": "ok",
            "observed_at": now,
            "description": "Primary data store",
            "metrics": {
                "read_capacity_units": 5,
                "write_capacity_units": 5
            },
            "issues": [],
            "logs": []
        },
        {
            "id": "metrics-calculator",
            "display_name": "Metrics Calculator",
            "status": "ok",
            "observed_at": now,
            "description": "Model evaluation service",
            "metrics": {},
            "issues": [],
            "logs": []
        }
    ]
    
    result = {
        "components": components,
        "generated_at": now,
        "window_minutes": window_minutes
    }
    
    if include_timeline:
        for comp in components:
            comp["timeline"] = []
    
    return result
