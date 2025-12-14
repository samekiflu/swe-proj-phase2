"""
Bus Factor Metric Calculator
Evaluates maintainer activity and project health
"""
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from src.models.model import ModelInfo, MetricResult


class BusFactorMetric:
    """Calculate bus factor / maintainer reliability score"""
    
    # Known organizations with high reliability
    TRUSTED_ORGS = {
        "google": 0.95,
        "openai": 0.95,
        "meta": 0.9,
        "facebook": 0.9,
        "microsoft": 0.9,
        "nvidia": 0.9,
        "huggingface": 0.9,
        "stability-ai": 0.85,
        "stabilityai": 0.85,
        "mistral": 0.85,
        "mistralai": 0.85,
        "anthropic": 0.9,
        "bigscience": 0.85,
        "eleutherai": 0.8,
        "allenai": 0.85,
        "amazon": 0.9,
        "salesforce": 0.85,
        "deepmind": 0.95,
        "databricks": 0.85,
        "cohere": 0.85,
    }
    
    def calculate(self, model_info: ModelInfo) -> MetricResult:
        """Calculate bus factor score"""
        start_time = time.time()
        
        scores = {
            "org_reliability": self._score_organization(model_info),
            "recent_activity": self._score_activity(model_info),
            "community_engagement": self._score_community(model_info),
        }
        
        # Weighted average
        # 30% org, 40% activity, 30% community
        final_score = (
            scores["org_reliability"] * 0.3 +
            scores["recent_activity"] * 0.4 +
            scores["community_engagement"] * 0.3
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="bus_factor",
            value=final_score,
            latency_ms=latency_ms,
            details={
                "component_scores": scores,
                "final_score": final_score
            }
        )
    
    def _score_organization(self, model_info: ModelInfo) -> float:
        """Score based on organization/author reputation"""
        name = model_info.name.lower()
        
        # Check if model is from a known org
        for org, score in self.TRUSTED_ORGS.items():
            if name.startswith(f"{org}/") or f"/{org}/" in name:
                return score
        
        # Extract organization from name
        if "/" in name:
            org = name.split("/")[0]
            if org in self.TRUSTED_ORGS:
                return self.TRUSTED_ORGS[org]
        
        # Check tags for organization hints
        for tag in model_info.tags:
            tag_lower = tag.lower()
            for org, score in self.TRUSTED_ORGS.items():
                if org in tag_lower:
                    return score * 0.9  # Slight discount for indirect association
        
        # Default score for unknown orgs
        return 0.5
    
    def _score_activity(self, model_info: ModelInfo) -> float:
        """Score based on recent activity"""
        last_modified = model_info.last_modified
        
        if not last_modified:
            api_data = model_info.api_data or {}
            last_modified = api_data.get("lastModified", "")
        
        if not last_modified:
            return 0.4  # Unknown activity
        
        try:
            # Parse ISO format date
            if "T" in last_modified:
                mod_date = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
            else:
                mod_date = datetime.strptime(last_modified[:10], "%Y-%m-%d")
            
            now = datetime.now(mod_date.tzinfo) if mod_date.tzinfo else datetime.now()
            days_since = (now - mod_date).days
            
            if days_since <= 7:
                return 1.0
            elif days_since <= 30:
                return 0.9
            elif days_since <= 90:
                return 0.8
            elif days_since <= 180:
                return 0.6
            elif days_since <= 365:
                return 0.4
            else:
                return 0.3
                
        except Exception:
            return 0.4
    
    def _score_community(self, model_info: ModelInfo) -> float:
        """Score based on community engagement"""
        downloads = model_info.downloads
        likes = model_info.likes
        
        # Combined engagement score
        if downloads >= 1000000 and likes >= 1000:
            return 1.0
        elif downloads >= 100000 and likes >= 100:
            return 0.9
        elif downloads >= 10000 and likes >= 50:
            return 0.8
        elif downloads >= 1000 and likes >= 10:
            return 0.6
        elif downloads >= 100:
            return 0.4
        else:
            return 0.3
