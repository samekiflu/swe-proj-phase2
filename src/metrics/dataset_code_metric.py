"""
Dataset and Code Score Metric Calculator
Evaluates availability of training data and code
"""
import time
import re
from typing import Dict, Any, List
from src.models.model import ModelInfo, MetricResult


class DatasetCodeMetric:
    """Calculate score based on training data and code availability"""
    
    def calculate(self, model_info: ModelInfo) -> MetricResult:
        """Calculate dataset and code availability score"""
        start_time = time.time()
        
        scores = {
            "dataset_linked": self._score_datasets(model_info),
            "code_linked": self._score_code(model_info),
            "training_info": self._score_training_info(model_info),
        }
        
        # Weighted average
        # 40% datasets, 40% code, 20% training info
        final_score = (
            scores["dataset_linked"] * 0.4 +
            scores["code_linked"] * 0.4 +
            scores["training_info"] * 0.2
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="dataset_and_code_score",
            value=final_score,
            latency_ms=latency_ms,
            details={
                "component_scores": scores,
                "final_score": final_score
            }
        )
    
    def _score_datasets(self, model_info: ModelInfo) -> float:
        """Score based on linked datasets"""
        api_data = model_info.api_data or {}
        score = 0.3
        
        # Check cardData for datasets
        card_data = api_data.get("cardData", {})
        if isinstance(card_data, dict):
            datasets = card_data.get("datasets", [])
            if datasets:
                score += min(len(datasets) * 0.15, 0.4)
        
        # Check tags for dataset references
        for tag in model_info.tags:
            if tag.startswith("dataset:"):
                score += 0.15
        
        # Check README for dataset mentions
        readme = model_info.readme.lower() if model_info.readme else ""
        dataset_patterns = [
            r'trained\s+on\s+([a-z0-9_\-]+)',
            r'fine.?tuned\s+on\s+([a-z0-9_\-]+)',
            r'dataset[:\s]+([a-z0-9_\-]+)',
            r'huggingface\.co/datasets/',
        ]
        for pattern in dataset_patterns:
            if re.search(pattern, readme):
                score += 0.1
        
        return min(score, 1.0)
    
    def _score_code(self, model_info: ModelInfo) -> float:
        """Score based on linked code repositories"""
        api_data = model_info.api_data or {}
        readme = model_info.readme.lower() if model_info.readme else ""
        score = 0.3
        
        # Check for GitHub links
        github_pattern = r'github\.com/[a-z0-9_\-]+/[a-z0-9_\-]+'
        github_links = re.findall(github_pattern, readme, re.IGNORECASE)
        if github_links:
            score += min(len(github_links) * 0.2, 0.4)
        
        # Check siblings for code files
        siblings = api_data.get("siblings", [])
        code_extensions = [".py", ".ipynb", ".sh", ".yaml", ".yml", ".json"]
        code_files = 0
        for sib in siblings:
            filename = sib.get("rfilename", "") if isinstance(sib, dict) else ""
            if any(filename.endswith(ext) for ext in code_extensions):
                code_files += 1
        
        if code_files >= 3:
            score += 0.3
        elif code_files >= 1:
            score += 0.15
        
        return min(score, 1.0)
    
    def _score_training_info(self, model_info: ModelInfo) -> float:
        """Score based on training information availability"""
        readme = model_info.readme.lower() if model_info.readme else ""
        score = 0.3
        
        # Check for training documentation
        training_keywords = [
            "training", "fine-tuning", "fine tuning", "hyperparameter",
            "learning rate", "batch size", "epochs", "optimizer",
            "training script", "training code", "reproduce"
        ]
        
        matches = sum(1 for kw in training_keywords if kw in readme)
        score += min(matches * 0.1, 0.5)
        
        # Check for config files
        api_data = model_info.api_data or {}
        siblings = api_data.get("siblings", [])
        config_files = ["config.json", "training_args.bin", "trainer_state.json"]
        for sib in siblings:
            filename = sib.get("rfilename", "") if isinstance(sib, dict) else ""
            if filename in config_files:
                score += 0.1
        
        return min(score, 1.0)
