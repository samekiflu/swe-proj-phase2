"""
Ramp-Up Time Metric Calculator
Evaluates documentation quality and ease of adoption
"""
import time
import re
from typing import Dict, Any, List
from src.models.model import ModelInfo, MetricResult


class RampUpMetric:
    """Calculate ease-of-adoption score based on documentation quality"""
    
    def calculate(self, model_info: ModelInfo) -> MetricResult:
        """Calculate ramp-up time score"""
        start_time = time.time()
        
        scores = {
            "readme_quality": self._score_readme(model_info),
            "examples": self._score_examples(model_info),
            "model_card": self._score_model_card(model_info),
            "popularity": self._score_popularity(model_info),
        }
        
        # Weighted average
        # 40% README, 30% examples, 20% model card, 10% popularity
        final_score = (
            scores["readme_quality"] * 0.4 +
            scores["examples"] * 0.3 +
            scores["model_card"] * 0.2 +
            scores["popularity"] * 0.1
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="ramp_up_time",
            value=final_score,
            latency_ms=latency_ms,
            details={
                "component_scores": scores,
                "final_score": final_score
            }
        )
    
    def _score_readme(self, model_info: ModelInfo) -> float:
        """Score README quality (40% of total)"""
        readme = model_info.readme.lower() if model_info.readme else ""
        
        if not readme:
            # Check API data for description
            api_data = model_info.api_data or {}
            readme = str(api_data.get("description", "")).lower()
        
        if not readme:
            return 0.3  # Minimal score for missing README
        
        score = 0.3  # Base score for having a README
        
        # Check for key sections
        sections = {
            "usage": ["usage", "how to use", "getting started", "quick start"],
            "installation": ["install", "pip install", "requirements", "dependencies"],
            "examples": ["example", "sample", "demo", "```python", "```"],
            "description": ["description", "overview", "about", "introduction"],
            "performance": ["performance", "benchmark", "accuracy", "results", "evaluation"],
        }
        
        for section_name, keywords in sections.items():
            if any(kw in readme for kw in keywords):
                score += 0.12
        
        # Bonus for code blocks
        code_blocks = readme.count("```")
        if code_blocks >= 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_examples(self, model_info: ModelInfo) -> float:
        """Score availability of examples (30% of total)"""
        score = 0.3
        
        readme = model_info.readme.lower() if model_info.readme else ""
        api_data = model_info.api_data or {}
        
        # Check for code examples in README
        if "```python" in readme or ">>> " in readme:
            score += 0.3
        
        # Check for example files in siblings
        siblings = api_data.get("siblings", [])
        example_files = ["example", "demo", "sample", "notebook", ".ipynb"]
        for sib in siblings:
            filename = sib.get("rfilename", "") if isinstance(sib, dict) else ""
            if any(ef in filename.lower() for ef in example_files):
                score += 0.2
                break
        
        # Check pipeline_tag (indicates easy-to-use interface)
        if model_info.pipeline_tag:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_model_card(self, model_info: ModelInfo) -> float:
        """Score model card completeness (20% of total)"""
        score = 0.2
        
        api_data = model_info.api_data or {}
        
        # Has pipeline tag
        if model_info.pipeline_tag:
            score += 0.2
        
        # Has tags
        if len(model_info.tags) >= 3:
            score += 0.15
        
        # Has model index (benchmark results)
        if model_info.model_index:
            score += 0.25
        
        # Has license
        if model_info.license and model_info.license != "unknown":
            score += 0.1
        
        # Has library name
        if model_info.library_name:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_popularity(self, model_info: ModelInfo) -> float:
        """Score based on popularity (10% of total)"""
        downloads = model_info.downloads
        likes = model_info.likes
        
        # Downloads scoring (log scale)
        if downloads >= 1000000:
            download_score = 1.0
        elif downloads >= 100000:
            download_score = 0.8
        elif downloads >= 10000:
            download_score = 0.6
        elif downloads >= 1000:
            download_score = 0.4
        else:
            download_score = 0.2
        
        # Likes scoring
        if likes >= 1000:
            like_score = 1.0
        elif likes >= 100:
            like_score = 0.7
        elif likes >= 10:
            like_score = 0.4
        else:
            like_score = 0.2
        
        return (download_score * 0.7 + like_score * 0.3)
