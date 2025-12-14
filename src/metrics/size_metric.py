"""
Size Metric Calculator
Evaluates model size against hardware constraints
"""
import time
import re
from typing import Dict, Any
from src.models.model import ModelInfo, MetricResult, SizeScore


class SizeMetric:
    """Calculate hardware compatibility scores based on model size"""
    
    # Hardware memory limits in bytes
    HARDWARE_LIMITS = {
        "raspberry_pi": 1 * 1024 * 1024 * 1024,      # 1 GB
        "jetson_nano": 4 * 1024 * 1024 * 1024,       # 4 GB
        "desktop_pc": 16 * 1024 * 1024 * 1024,       # 16 GB
        "aws_server": 64 * 1024 * 1024 * 1024,       # 64 GB
    }
    
    # Estimated sizes for model name patterns (in bytes)
    SIZE_PATTERNS = {
        "7b": 13 * 1024 * 1024 * 1024,    # ~13 GB
        "13b": 26 * 1024 * 1024 * 1024,   # ~26 GB
        "30b": 60 * 1024 * 1024 * 1024,   # ~60 GB
        "65b": 130 * 1024 * 1024 * 1024,  # ~130 GB
        "70b": 140 * 1024 * 1024 * 1024,  # ~140 GB
        "tiny": 100 * 1024 * 1024,         # ~100 MB
        "small": 500 * 1024 * 1024,        # ~500 MB
        "base": 500 * 1024 * 1024,         # ~500 MB
        "medium": 1.5 * 1024 * 1024 * 1024, # ~1.5 GB
        "large": 3 * 1024 * 1024 * 1024,   # ~3 GB
        "xl": 6 * 1024 * 1024 * 1024,      # ~6 GB
        "xxl": 12 * 1024 * 1024 * 1024,    # ~12 GB
    }
    
    def calculate(self, model_info: ModelInfo) -> MetricResult:
        """Calculate size scores for all hardware targets"""
        start_time = time.time()
        
        # Estimate model size
        size_bytes = self._estimate_size(model_info)
        
        # Calculate scores for each hardware target
        size_score = SizeScore()
        
        for hw_name, hw_limit in self.HARDWARE_LIMITS.items():
            score = self._calculate_hardware_score(size_bytes, hw_limit)
            setattr(size_score, hw_name, score)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="size_score",
            value=self._average_score(size_score),
            latency_ms=latency_ms,
            details={
                "estimated_size_bytes": size_bytes,
                "estimated_size_gb": round(size_bytes / (1024**3), 2),
                "hardware_scores": size_score.to_dict()
            }
        )
    
    def get_size_score(self, model_info: ModelInfo) -> SizeScore:
        """Get just the SizeScore object"""
        result = self.calculate(model_info)
        return SizeScore(**result.details["hardware_scores"])
    
    def _estimate_size(self, model_info: ModelInfo) -> int:
        """Estimate model size from various sources"""
        
        # 1. Direct size from siblings (file list)
        if model_info.total_size_bytes > 0:
            return model_info.total_size_bytes
        
        # 2. From API data siblings
        api_data = model_info.api_data or {}
        siblings = api_data.get("siblings", [])
        if siblings:
            total = sum(f.get("size", 0) for f in siblings if isinstance(f, dict))
            if total > 0:
                return total
        
        # 3. Estimate from model name patterns
        name_lower = model_info.name.lower()
        
        for pattern, size in self.SIZE_PATTERNS.items():
            if pattern in name_lower:
                return int(size)
        
        # 4. Estimate from library name
        library = model_info.library_name.lower() if model_info.library_name else ""
        
        if "sentence-transformer" in library or "sentence-transformer" in name_lower:
            return 500 * 1024 * 1024  # ~500 MB typical
        if "bert" in name_lower:
            return 500 * 1024 * 1024  # ~500 MB for BERT base
        if "gpt2" in name_lower and "xl" not in name_lower:
            return 600 * 1024 * 1024  # ~600 MB for GPT-2 base
        if "whisper" in name_lower:
            if "tiny" in name_lower:
                return 150 * 1024 * 1024
            elif "small" in name_lower:
                return 500 * 1024 * 1024
            elif "medium" in name_lower:
                return 1.5 * 1024 * 1024 * 1024
            elif "large" in name_lower:
                return 3 * 1024 * 1024 * 1024
            return 500 * 1024 * 1024
        
        # Default estimate based on downloads (popular models tend to be smaller)
        downloads = model_info.downloads
        if downloads > 1000000:  # Very popular, likely small/efficient
            return 500 * 1024 * 1024
        elif downloads > 100000:
            return 1 * 1024 * 1024 * 1024
        elif downloads > 10000:
            return 2 * 1024 * 1024 * 1024
        
        # Conservative default
        return 2 * 1024 * 1024 * 1024  # 2 GB default
    
    def _calculate_hardware_score(self, size_bytes: int, limit_bytes: int) -> float:
        """
        Calculate score for a specific hardware target
        1.0 = Fits easily (<50% of limit)
        0.5 = Fits but tight (50-100% of limit)
        0.0 = Doesn't fit (>100% of limit)
        """
        if size_bytes <= 0:
            return 1.0
        
        ratio = size_bytes / limit_bytes
        
        if ratio <= 0.25:
            return 1.0
        elif ratio <= 0.5:
            return 0.9
        elif ratio <= 0.75:
            return 0.7
        elif ratio <= 1.0:
            return 0.5
        elif ratio <= 1.5:
            return 0.2
        else:
            return 0.0
    
    def _average_score(self, size_score: SizeScore) -> float:
        """Calculate average score across all hardware"""
        scores = [
            size_score.raspberry_pi,
            size_score.jetson_nano,
            size_score.desktop_pc,
            size_score.aws_server
        ]
        return sum(scores) / len(scores)
