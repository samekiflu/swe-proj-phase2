"""
Dataset Quality Metric Calculator
Evaluates quality of training data
"""
import time
import re
from typing import Dict, Any
from src.models.model import ModelInfo, MetricResult


class DatasetQualityMetric:
    """Calculate score based on training dataset quality"""
    
    # Known high-quality datasets
    QUALITY_DATASETS = {
        "wikipedia": 0.9,
        "bookcorpus": 0.8,
        "c4": 0.85,
        "openwebtext": 0.8,
        "pile": 0.85,
        "redpajama": 0.85,
        "squad": 0.9,
        "glue": 0.9,
        "superglue": 0.9,
        "imagenet": 0.95,
        "coco": 0.9,
        "laion": 0.75,
        "common_crawl": 0.7,
        "librispeech": 0.9,
        "common_voice": 0.85,
    }
    
    def calculate(self, model_info: ModelInfo) -> MetricResult:
        """Calculate dataset quality score"""
        start_time = time.time()
        
        scores = {
            "known_datasets": self._score_known_datasets(model_info),
            "dataset_documentation": self._score_documentation(model_info),
            "data_curation": self._score_curation(model_info),
        }
        
        # Weighted average
        final_score = (
            scores["known_datasets"] * 0.5 +
            scores["dataset_documentation"] * 0.3 +
            scores["data_curation"] * 0.2
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="dataset_quality",
            value=final_score,
            latency_ms=latency_ms,
            details={
                "component_scores": scores,
                "final_score": final_score
            }
        )
    
    def _score_known_datasets(self, model_info: ModelInfo) -> float:
        """Score based on known high-quality datasets"""
        api_data = model_info.api_data or {}
        readme = model_info.readme.lower() if model_info.readme else ""
        tags = [t.lower() for t in model_info.tags]
        
        # Collect all text to search
        search_text = readme + " " + " ".join(tags)
        card_data = api_data.get("cardData", {})
        if isinstance(card_data, dict):
            datasets = card_data.get("datasets", [])
            if datasets:
                search_text += " " + " ".join(str(d).lower() for d in datasets)
        
        # Find quality datasets
        max_quality = 0.4  # Base score
        for dataset, quality in self.QUALITY_DATASETS.items():
            if dataset in search_text:
                max_quality = max(max_quality, quality)
        
        return max_quality
    
    def _score_documentation(self, model_info: ModelInfo) -> float:
        """Score based on dataset documentation"""
        readme = model_info.readme.lower() if model_info.readme else ""
        score = 0.3
        
        # Check for data documentation
        doc_keywords = [
            "data collection", "data source", "data preprocessing",
            "data cleaning", "data filtering", "dataset size",
            "training data", "data quality", "data curation"
        ]
        
        matches = sum(1 for kw in doc_keywords if kw in readme)
        score += min(matches * 0.1, 0.5)
        
        # Check for data statistics
        if re.search(r'\b\d+[kmbt]?\s*(samples|examples|instances|records)', readme):
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_curation(self, model_info: ModelInfo) -> float:
        """Score based on evidence of data curation"""
        readme = model_info.readme.lower() if model_info.readme else ""
        score = 0.4
        
        # Check for curation keywords
        curation_keywords = [
            "curated", "filtered", "cleaned", "quality control",
            "human review", "annotation", "labeled", "verified"
        ]
        
        matches = sum(1 for kw in curation_keywords if kw in readme)
        score += min(matches * 0.15, 0.4)
        
        # Check for bias/ethics considerations
        if any(kw in readme for kw in ["bias", "fairness", "ethics", "limitations"]):
            score += 0.2
        
        return min(score, 1.0)
