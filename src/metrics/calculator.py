"""
Metrics Calculator - Orchestrates all metric calculations
"""
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import Dict, Any, Optional

from src.models.model import ModelInfo, ModelRating, SizeScore, MetricResult
from .license_metric import LicenseMetric
from .size_metric import SizeMetric
from .rampup_metric import RampUpMetric
from .busfactor_metric import BusFactorMetric
from .performance_metric import PerformanceMetric
from .dataset_code_metric import DatasetCodeMetric
from .dataset_quality_metric import DatasetQualityMetric
from .code_quality_metric import CodeQualityMetric

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Orchestrates parallel calculation of all metrics"""
    
    # Weights for net score calculation
    WEIGHTS = {
        "license": 0.15,
        "ramp_up_time": 0.20,
        "bus_factor": 0.10,
        "performance_claims": 0.15,
        "dataset_and_code_score": 0.20,
        "dataset_quality": 0.10,
        "code_quality": 0.10,
    }
    
    def __init__(self):
        self.max_workers = min(8, cpu_count())
        self.license_metric = LicenseMetric()
        self.size_metric = SizeMetric()
        self.rampup_metric = RampUpMetric()
        self.busfactor_metric = BusFactorMetric()
        self.performance_metric = PerformanceMetric()
        self.dataset_code_metric = DatasetCodeMetric()
        self.dataset_quality_metric = DatasetQualityMetric()
        self.code_quality_metric = CodeQualityMetric()
    
    def calculate_all_metrics(self, model_info: ModelInfo) -> Dict[str, Any]:
        """
        Calculate all metrics for a model in parallel
        Returns a dictionary with all scores and latencies
        """
        start_time = time.time()
        
        results = {}
        
        # Define metric calculations
        metric_funcs = {
            "license": lambda: self.license_metric.calculate(model_info),
            "ramp_up_time": lambda: self.rampup_metric.calculate(model_info),
            "bus_factor": lambda: self.busfactor_metric.calculate(model_info),
            "performance_claims": lambda: self.performance_metric.calculate(model_info),
            "dataset_and_code_score": lambda: self.dataset_code_metric.calculate(model_info),
            "dataset_quality": lambda: self.dataset_quality_metric.calculate(model_info),
            "code_quality": lambda: self.code_quality_metric.calculate(model_info),
            "size_score": lambda: self.size_metric.calculate(model_info),
        }
        
        # Calculate metrics in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_metric = {
                executor.submit(func): name 
                for name, func in metric_funcs.items()
            }
            
            for future in as_completed(future_to_metric):
                metric_name = future_to_metric[future]
                try:
                    result = future.result()
                    results[metric_name] = result
                except Exception as e:
                    logger.error(f"Error calculating {metric_name}: {e}")
                    # Default result on error
                    results[metric_name] = MetricResult(
                        name=metric_name,
                        value=0.5,
                        latency_ms=0,
                        details={"error": str(e)}
                    )
        
        # Calculate net score
        net_score = self._calculate_net_score(results)
        total_latency_ms = int((time.time() - start_time) * 1000)
        
        # Build output dictionary
        output = {
            "name": model_info.name,
            "category": self._determine_category(model_info),
            "net_score": net_score,
            "net_score_latency": total_latency_ms / 1000,  # Convert to seconds
        }
        
        # Add individual metric scores and latencies
        for metric_name, result in results.items():
            if metric_name == "size_score":
                # Handle size_score specially (it's a dict)
                output["size_score"] = result.details.get("hardware_scores", {
                    "raspberry_pi": 0.5,
                    "jetson_nano": 0.5,
                    "desktop_pc": 0.5,
                    "aws_server": 0.5
                })
                output["size_score_latency"] = result.latency_ms / 1000
            else:
                output[metric_name] = result.value
                output[f"{metric_name}_latency"] = result.latency_ms / 1000
        
        # Add reproducibility and reviewedness (derived metrics)
        output["reproducibility"] = self._calculate_reproducibility(results)
        output["reproducibility_latency"] = 0.001
        output["reviewedness"] = self._calculate_reviewedness(results)
        output["reviewedness_latency"] = 0.001
        output["tree_score"] = self._calculate_tree_score(results)
        output["tree_score_latency"] = 0.001
        
        return output
    
    def _calculate_net_score(self, results: Dict[str, MetricResult]) -> float:
        """Calculate weighted net score from all metrics"""
        total_weight = 0
        weighted_sum = 0
        
        for metric_name, weight in self.WEIGHTS.items():
            if metric_name in results:
                weighted_sum += results[metric_name].value * weight
                total_weight += weight
        
        if total_weight > 0:
            return round(weighted_sum / total_weight, 4)
        return 0.5
    
    def _determine_category(self, model_info: ModelInfo) -> str:
        """Determine model category from metadata"""
        pipeline_tag = model_info.pipeline_tag
        if pipeline_tag:
            return pipeline_tag
        
        # Infer from tags
        tags = [t.lower() for t in model_info.tags]
        
        category_keywords = {
            "text-generation": ["text-generation", "gpt", "llm", "causal-lm"],
            "text-classification": ["text-classification", "sentiment", "classifier"],
            "question-answering": ["question-answering", "qa", "squad"],
            "translation": ["translation", "nmt", "mt"],
            "summarization": ["summarization", "summary"],
            "image-classification": ["image-classification", "vision", "resnet", "vit"],
            "object-detection": ["object-detection", "yolo", "detection"],
            "speech-recognition": ["speech-recognition", "asr", "whisper", "wav2vec"],
            "text-to-speech": ["text-to-speech", "tts"],
            "feature-extraction": ["feature-extraction", "embedding", "sentence-transformer"],
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in tag for tag in tags for kw in keywords):
                return category
        
        return "unknown"
    
    def _calculate_reproducibility(self, results: Dict[str, MetricResult]) -> float:
        """Calculate reproducibility score (derived from other metrics)"""
        # Based on dataset/code availability and documentation
        dataset_score = results.get("dataset_and_code_score", MetricResult("", 0.5, 0)).value
        code_quality = results.get("code_quality", MetricResult("", 0.5, 0)).value
        rampup = results.get("ramp_up_time", MetricResult("", 0.5, 0)).value
        
        return round((dataset_score * 0.4 + code_quality * 0.3 + rampup * 0.3), 4)
    
    def _calculate_reviewedness(self, results: Dict[str, MetricResult]) -> float:
        """Calculate reviewedness score (derived from community engagement)"""
        bus_factor = results.get("bus_factor", MetricResult("", 0.5, 0)).value
        performance = results.get("performance_claims", MetricResult("", 0.5, 0)).value
        
        return round((bus_factor * 0.5 + performance * 0.5), 4)
    
    def _calculate_tree_score(self, results: Dict[str, MetricResult]) -> float:
        """Calculate tree/supply-chain score"""
        license_score = results.get("license", MetricResult("", 0.5, 0)).value
        code_quality = results.get("code_quality", MetricResult("", 0.5, 0)).value
        
        return round((license_score * 0.6 + code_quality * 0.4), 4)
    
    def get_model_rating(self, model_info: ModelInfo) -> ModelRating:
        """Get a ModelRating object with all metrics"""
        metrics = self.calculate_all_metrics(model_info)
        
        size_score_dict = metrics.get("size_score", {})
        size_score = SizeScore(
            raspberry_pi=size_score_dict.get("raspberry_pi", 0.5),
            jetson_nano=size_score_dict.get("jetson_nano", 0.5),
            desktop_pc=size_score_dict.get("desktop_pc", 0.5),
            aws_server=size_score_dict.get("aws_server", 0.5)
        )
        
        return ModelRating(
            name=metrics["name"],
            category=metrics["category"],
            net_score=metrics["net_score"],
            net_score_latency=metrics["net_score_latency"],
            license=metrics.get("license", 0.5),
            license_latency=metrics.get("license_latency", 0.001),
            ramp_up_time=metrics.get("ramp_up_time", 0.5),
            ramp_up_time_latency=metrics.get("ramp_up_time_latency", 0.001),
            bus_factor=metrics.get("bus_factor", 0.5),
            bus_factor_latency=metrics.get("bus_factor_latency", 0.001),
            performance_claims=metrics.get("performance_claims", 0.5),
            performance_claims_latency=metrics.get("performance_claims_latency", 0.001),
            dataset_and_code_score=metrics.get("dataset_and_code_score", 0.5),
            dataset_and_code_score_latency=metrics.get("dataset_and_code_score_latency", 0.001),
            dataset_quality=metrics.get("dataset_quality", 0.5),
            dataset_quality_latency=metrics.get("dataset_quality_latency", 0.001),
            code_quality=metrics.get("code_quality", 0.5),
            code_quality_latency=metrics.get("code_quality_latency", 0.001),
            reproducibility=metrics.get("reproducibility", 0.5),
            reproducibility_latency=metrics.get("reproducibility_latency", 0.001),
            reviewedness=metrics.get("reviewedness", 0.5),
            reviewedness_latency=metrics.get("reviewedness_latency", 0.001),
            tree_score=metrics.get("tree_score", 0.5),
            tree_score_latency=metrics.get("tree_score_latency", 0.001),
            size_score=size_score,
            size_score_latency=metrics.get("size_score_latency", 0.001)
        )


# Threshold check for ingest
def check_ingest_threshold(metrics: Dict[str, Any], threshold: float = 0.5) -> bool:
    """
    Check if all non-latency metrics meet the minimum threshold
    """
    NON_LATENCY_KEYS = [
        "net_score", "ramp_up_time", "bus_factor", "performance_claims",
        "license", "dataset_and_code_score", "dataset_quality", "code_quality",
        "reproducibility", "reviewedness", "tree_score"
    ]
    
    for key in NON_LATENCY_KEYS:
        value = metrics.get(key, 0)
        try:
            if float(value) < threshold:
                return False
        except (TypeError, ValueError):
            return False
    
    # Check size_score
    size_score = metrics.get("size_score", {})
    if isinstance(size_score, dict):
        for hw_value in size_score.values():
            try:
                if float(hw_value) < threshold:
                    return False
            except (TypeError, ValueError):
                return False
    
    return True
