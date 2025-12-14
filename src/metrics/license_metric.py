"""
License Metric Calculator
Evaluates license compatibility with LGPLv2.1
"""
import time
import re
from typing import Dict, Any, Optional
from src.models.model import ModelInfo, MetricResult


class LicenseMetric:
    """Calculate license compatibility score"""
    
    # License compatibility scores (higher = more permissive/compatible)
    LICENSE_SCORES = {
        # Very permissive
        "mit": 1.0,
        "bsd-3-clause": 1.0,
        "bsd-2-clause": 1.0,
        "bsd": 1.0,
        "apache-2.0": 0.9,
        "apache": 0.9,
        "unlicense": 1.0,
        "cc0-1.0": 1.0,
        "wtfpl": 1.0,
        "isc": 1.0,
        
        # Somewhat permissive
        "cc-by-4.0": 0.8,
        "cc-by-sa-4.0": 0.7,
        "openrail": 0.8,
        "openrail++": 0.8,
        "bigscience-openrail-m": 0.75,
        "creativeml-openrail-m": 0.75,
        "llama2": 0.7,
        "llama3": 0.7,
        "gemma": 0.7,
        
        # Copyleft (more restrictive)
        "lgpl-2.1": 0.6,
        "lgpl-3.0": 0.6,
        "lgpl": 0.6,
        "mpl-2.0": 0.6,
        "gpl-2.0": 0.3,
        "gpl-3.0": 0.3,
        "gpl": 0.3,
        "agpl-3.0": 0.2,
        "agpl": 0.2,
        
        # Non-commercial
        "cc-by-nc-4.0": 0.4,
        "cc-by-nc-sa-4.0": 0.3,
        "cc-by-nc-nd-4.0": 0.2,
        
        # Unknown/Other
        "other": 0.3,
        "unknown": 0.1,
    }
    
    def calculate(self, model_info: ModelInfo) -> MetricResult:
        """Calculate license score for a model"""
        start_time = time.time()
        
        # Try to get license from multiple sources
        license_str = self._extract_license(model_info)
        
        # Normalize and score
        normalized = self._normalize_license(license_str)
        score = self._score_license(normalized)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="license",
            value=score,
            latency_ms=latency_ms,
            details={
                "license_detected": license_str,
                "license_normalized": normalized,
                "score": score
            }
        )
    
    def _extract_license(self, model_info: ModelInfo) -> str:
        """Extract license from model info"""
        # 1. Direct license field
        if model_info.license:
            return model_info.license
        
        # 2. From API data
        api_data = model_info.api_data or {}
        if "license" in api_data:
            return api_data["license"]
        
        # 3. From cardData
        card_data = api_data.get("cardData", {})
        if isinstance(card_data, dict) and "license" in card_data:
            return card_data["license"]
        
        # 4. From tags
        for tag in model_info.tags:
            tag_lower = tag.lower()
            if "license:" in tag_lower:
                return tag.split(":", 1)[1].strip()
        
        # 5. Parse from README
        if model_info.readme:
            license_match = re.search(
                r'license[:\s]+([a-z0-9\-\.]+)',
                model_info.readme.lower()
            )
            if license_match:
                return license_match.group(1)
        
        return "unknown"
    
    def _normalize_license(self, license_str: str) -> str:
        """Normalize license string for lookup"""
        if not license_str:
            return "unknown"
        
        normalized = license_str.lower().strip()
        
        # Common normalizations
        normalized = normalized.replace(" ", "-")
        normalized = normalized.replace("_", "-")
        
        # Handle variations
        if "apache" in normalized and "2" in normalized:
            return "apache-2.0"
        if normalized in ("mit", "mit-license"):
            return "mit"
        if "bsd" in normalized:
            if "3" in normalized:
                return "bsd-3-clause"
            elif "2" in normalized:
                return "bsd-2-clause"
            return "bsd"
        if "gpl" in normalized:
            if "lgpl" in normalized:
                if "3" in normalized:
                    return "lgpl-3.0"
                return "lgpl-2.1"
            if "agpl" in normalized:
                return "agpl-3.0"
            if "3" in normalized:
                return "gpl-3.0"
            return "gpl-2.0"
        
        return normalized
    
    def _score_license(self, normalized_license: str) -> float:
        """Get score for normalized license"""
        if normalized_license in self.LICENSE_SCORES:
            return self.LICENSE_SCORES[normalized_license]
        
        # Partial matches
        for key, score in self.LICENSE_SCORES.items():
            if key in normalized_license or normalized_license in key:
                return score
        
        return 0.3  # Default for unknown licenses


def check_license_compatibility(license1: str, license2: str) -> bool:
    """
    Check if two licenses are compatible for use together
    """
    metric = LicenseMetric()
    l1 = metric._normalize_license(license1)
    l2 = metric._normalize_license(license2)
    
    # Very permissive licenses are compatible with everything
    permissive = {"mit", "bsd", "bsd-2-clause", "bsd-3-clause", "apache-2.0", "unlicense", "cc0-1.0"}
    
    if l1 in permissive or l2 in permissive:
        return True
    
    # Same license family is compatible
    if l1 == l2:
        return True
    
    # GPL family compatibility
    gpl_family = {"gpl-2.0", "gpl-3.0", "lgpl-2.1", "lgpl-3.0"}
    if l1 in gpl_family and l2 in gpl_family:
        return True
    
    # OpenRAIL variants are compatible
    openrail = {"openrail", "openrail++", "bigscience-openrail-m", "creativeml-openrail-m"}
    if l1 in openrail and l2 in openrail:
        return True
    
    # Both permissive enough
    s1 = metric._score_license(l1)
    s2 = metric._score_license(l2)
    
    return s1 >= 0.7 and s2 >= 0.7
