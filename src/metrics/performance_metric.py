"""
Performance Claims Metric Calculator
Evaluates evidence of benchmarks and performance claims
"""
import time
import re
from typing import Dict, Any, List
from src.models.model import ModelInfo, MetricResult


class PerformanceMetric:
    """Calculate score based on performance evidence and benchmark results"""
    
    BENCHMARK_KEYWORDS = [
        "accuracy", "f1", "precision", "recall", "bleu", "rouge",
        "perplexity", "wer", "cer", "map", "iou", "auc", "roc",
        "benchmark", "evaluation", "performance", "results", "sota",
        "state-of-the-art", "leaderboard", "score", "metric"
    ]
    
    KNOWN_BENCHMARKS = [
        "squad", "glue", "superglue", "mmlu", "hellaswag", "arc",
        "winogrande", "truthfulqa", "gsm8k", "humaneval", "mbpp",
        "imagenet", "coco", "voc", "cityscapes", "librispeech",
        "common_voice", "wmt", "flores", "mteb"
    ]
    
    def calculate(self, model_info: ModelInfo) -> MetricResult:
        """Calculate performance evidence score"""
        start_time = time.time()
        
        scores = {
            "model_index": self._score_model_index(model_info),
            "readme_benchmarks": self._score_readme_benchmarks(model_info),
            "tags_evidence": self._score_tags(model_info),
        }
        
        # Weighted average
        # 50% model_index (structured data), 35% README, 15% tags
        final_score = (
            scores["model_index"] * 0.5 +
            scores["readme_benchmarks"] * 0.35 +
            scores["tags_evidence"] * 0.15
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="performance_claims",
            value=final_score,
            latency_ms=latency_ms,
            details={
                "component_scores": scores,
                "final_score": final_score
            }
        )
    
    def _score_model_index(self, model_info: ModelInfo) -> float:
        """Score based on model_index (evaluation results)"""
        model_index = model_info.model_index
        
        if not model_index:
            # Check API data
            api_data = model_info.api_data or {}
            model_index = api_data.get("model_index") or api_data.get("modelIndex") or []
        
        if not model_index:
            return 0.3
        
        # Has model index = has structured evaluation data
        score = 0.6
        
        # Check for multiple results
        total_results = 0
        for entry in model_index:
            if isinstance(entry, dict):
                results = entry.get("results", [])
                total_results += len(results) if isinstance(results, list) else 0
        
        if total_results >= 5:
            score += 0.4
        elif total_results >= 3:
            score += 0.3
        elif total_results >= 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_readme_benchmarks(self, model_info: ModelInfo) -> float:
        """Score based on benchmark mentions in README"""
        readme = model_info.readme.lower() if model_info.readme else ""
        
        if not readme:
            return 0.3
        
        score = 0.3
        
        # Check for benchmark keywords
        keyword_matches = sum(1 for kw in self.BENCHMARK_KEYWORDS if kw in readme)
        score += min(keyword_matches * 0.05, 0.3)
        
        # Check for known benchmarks
        benchmark_matches = sum(1 for bm in self.KNOWN_BENCHMARKS if bm in readme)
        score += min(benchmark_matches * 0.1, 0.3)
        
        # Check for numeric results (e.g., "accuracy: 95%")
        numeric_pattern = r'\b\d+\.?\d*\s*%|\b0\.\d+\b'
        numeric_matches = len(re.findall(numeric_pattern, readme))
        if numeric_matches >= 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_tags(self, model_info: ModelInfo) -> float:
        """Score based on tags indicating performance"""
        tags = [t.lower() for t in model_info.tags]
        
        score = 0.3
        
        # Check for evaluation/benchmark tags
        eval_tags = ["evaluation", "benchmark", "leaderboard", "sota"]
        if any(et in tag for tag in tags for et in eval_tags):
            score += 0.3
        
        # Check for dataset tags (implies evaluation)
        dataset_tags = ["dataset:", "trained_on:", "finetuned:"]
        if any(dt in tag for tag in tags for dt in dataset_tags):
            score += 0.2
        
        # Task-specific tags suggest evaluation
        task_tags = ["text-classification", "question-answering", "translation", 
                     "summarization", "text-generation", "image-classification"]
        if any(tt in tags for tt in task_tags):
            score += 0.2
        
        return min(score, 1.0)
