"""
Code Quality Metric Calculator
Evaluates code maintainability and quality
"""
import time
import re
from typing import Dict, Any
from src.models.model import ModelInfo, CodeInfo, MetricResult


class CodeQualityMetric:
    """Calculate code quality score"""
    
    def calculate(self, model_info: ModelInfo) -> MetricResult:
        """Calculate code quality score for a model"""
        start_time = time.time()
        
        scores = {
            "code_structure": self._score_code_structure(model_info),
            "documentation": self._score_code_documentation(model_info),
            "testing": self._score_testing(model_info),
        }
        
        # Weighted average
        final_score = (
            scores["code_structure"] * 0.4 +
            scores["documentation"] * 0.35 +
            scores["testing"] * 0.25
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="code_quality",
            value=final_score,
            latency_ms=latency_ms,
            details={
                "component_scores": scores,
                "final_score": final_score
            }
        )
    
    def calculate_for_repo(self, code_info: CodeInfo) -> MetricResult:
        """Calculate code quality score for a GitHub repo"""
        start_time = time.time()
        
        scores = {
            "repo_health": self._score_repo_health(code_info),
            "community": self._score_community(code_info),
            "maintenance": self._score_maintenance(code_info),
        }
        
        final_score = (
            scores["repo_health"] * 0.4 +
            scores["community"] * 0.3 +
            scores["maintenance"] * 0.3
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            name="code_quality",
            value=final_score,
            latency_ms=latency_ms,
            details={
                "component_scores": scores,
                "final_score": final_score
            }
        )
    
    def _score_code_structure(self, model_info: ModelInfo) -> float:
        """Score based on code structure in the model repo"""
        api_data = model_info.api_data or {}
        siblings = api_data.get("siblings", [])
        score = 0.4
        
        # Check for well-structured files
        good_files = {
            "config.json": 0.1,
            "tokenizer.json": 0.1,
            "tokenizer_config.json": 0.05,
            "special_tokens_map.json": 0.05,
            "model.safetensors": 0.1,
            "pytorch_model.bin": 0.1,
        }
        
        for sib in siblings:
            filename = sib.get("rfilename", "") if isinstance(sib, dict) else ""
            if filename in good_files:
                score += good_files[filename]
        
        # Check for Python files (indicates custom code)
        py_files = sum(1 for s in siblings 
                       if isinstance(s, dict) and s.get("rfilename", "").endswith(".py"))
        if py_files >= 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_code_documentation(self, model_info: ModelInfo) -> float:
        """Score based on code documentation"""
        readme = model_info.readme if model_info.readme else ""
        score = 0.3
        
        # Check for API documentation
        if "```python" in readme.lower():
            score += 0.2
        
        # Check for docstrings indication
        if "parameters" in readme.lower() or "arguments" in readme.lower():
            score += 0.15
        
        # Check for type hints mention
        if "type" in readme.lower() and ("hint" in readme.lower() or "annotation" in readme.lower()):
            score += 0.15
        
        # Check README length (longer = more docs)
        if len(readme) > 5000:
            score += 0.2
        elif len(readme) > 2000:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_testing(self, model_info: ModelInfo) -> float:
        """Score based on testing evidence"""
        api_data = model_info.api_data or {}
        siblings = api_data.get("siblings", [])
        readme = model_info.readme.lower() if model_info.readme else ""
        score = 0.3
        
        # Check for test files
        test_files = sum(1 for s in siblings 
                        if isinstance(s, dict) and 
                        ("test" in s.get("rfilename", "").lower() or
                         s.get("rfilename", "").startswith("test_")))
        if test_files >= 1:
            score += 0.3
        
        # Check README for testing info
        if "test" in readme or "pytest" in readme or "unittest" in readme:
            score += 0.2
        
        # Check for CI mentions
        if any(ci in readme for ci in ["github actions", "ci/cd", "continuous integration", "travis", "circleci"]):
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_repo_health(self, code_info: CodeInfo) -> float:
        """Score GitHub repo health"""
        score = 0.4
        
        # Stars indicate quality/popularity
        if code_info.stars >= 10000:
            score += 0.3
        elif code_info.stars >= 1000:
            score += 0.2
        elif code_info.stars >= 100:
            score += 0.1
        
        # Forks indicate usefulness
        if code_info.forks >= 1000:
            score += 0.2
        elif code_info.forks >= 100:
            score += 0.1
        
        # License indicates proper project setup
        if code_info.license and code_info.license != "unknown":
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_community(self, code_info: CodeInfo) -> float:
        """Score based on community engagement"""
        score = 0.4
        
        # Issue activity (some issues = active, too many = problems)
        issues = code_info.open_issues
        if 10 <= issues <= 100:
            score += 0.3
        elif issues < 10:
            score += 0.2
        elif issues <= 500:
            score += 0.1
        
        # Fork/star ratio (healthy ratio indicates usability)
        if code_info.stars > 0:
            ratio = code_info.forks / code_info.stars
            if 0.1 <= ratio <= 0.5:
                score += 0.3
            elif ratio < 0.1 or ratio <= 0.7:
                score += 0.2
        
        return min(score, 1.0)
    
    def _score_maintenance(self, code_info: CodeInfo) -> float:
        """Score based on maintenance activity"""
        from datetime import datetime
        
        score = 0.4
        last_updated = code_info.last_updated
        
        if not last_updated:
            return score
        
        try:
            update_date = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            now = datetime.now(update_date.tzinfo) if update_date.tzinfo else datetime.now()
            days_since = (now - update_date).days
            
            if days_since <= 30:
                score += 0.4
            elif days_since <= 90:
                score += 0.3
            elif days_since <= 180:
                score += 0.2
            elif days_since <= 365:
                score += 0.1
                
        except Exception:
            pass
        
        return min(score, 1.0)
