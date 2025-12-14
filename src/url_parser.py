"""
URL Parser for HuggingFace and GitHub URLs
Fetches metadata from external APIs
"""
import re
import os
import logging
from typing import Dict, Optional, Any
from urllib.parse import urlparse, unquote

try:
    import requests
except ImportError:
    requests = None

from src.models.model import ModelInfo, DatasetInfo, CodeInfo

logger = logging.getLogger(__name__)


class URLParser:
    """Parse HuggingFace and GitHub URLs and fetch metadata"""
    
    HF_API_BASE = "https://huggingface.co/api"
    GITHUB_API_BASE = "https://api.github.com"
    
    def __init__(self):
        self.hf_token = os.environ.get("HF_TOKEN", "")
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        self.timeout = 15
    
    def _get_headers(self, is_github: bool = False) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Accept": "application/json"}
        if is_github and self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        elif not is_github and self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"
        return headers
    
    def identify_url_type(self, url: str) -> str:
        """
        Identify URL type
        Returns: "MODEL", "DATASET", or "CODE"
        """
        url_lower = url.lower()
        
        if 'huggingface.co/datasets/' in url_lower:
            return "DATASET"
        elif 'github.com/' in url_lower:
            return "CODE"
        elif 'huggingface.co/' in url_lower:
            return "MODEL"
        else:
            return "UNKNOWN"
    
    def _extract_model_id(self, url: str) -> str:
        """Extract model ID from HuggingFace URL"""
        # Remove trailing slashes and /tree/main etc
        url = url.rstrip('/')
        url = re.sub(r'/tree/.*$', '', url)
        url = re.sub(r'/blob/.*$', '', url)
        
        # Match huggingface.co/org/model or huggingface.co/model
        match = re.search(r'huggingface\.co/([^?#]+)', url)
        if match:
            model_id = match.group(1)
            # Clean up the model_id
            model_id = model_id.strip('/')
            return model_id
        return ""
    
    def _extract_dataset_id(self, url: str) -> str:
        """Extract dataset ID from HuggingFace URL"""
        url = url.rstrip('/')
        match = re.search(r'huggingface\.co/datasets/([^?#/]+(?:/[^?#/]+)?)', url)
        if match:
            return match.group(1)
        return ""
    
    def _extract_github_info(self, url: str) -> tuple:
        """Extract owner and repo from GitHub URL"""
        url = url.rstrip('/')
        url = re.sub(r'\.git$', '', url)
        
        match = re.search(r'github\.com/([^/]+)/([^/?#]+)', url)
        if match:
            return match.group(1), match.group(2)
        return "", ""
    
    def parse_model_url(self, url: str) -> Optional[ModelInfo]:
        """Parse HuggingFace model URL and fetch metadata"""
        if not requests:
            logger.warning("requests library not available")
            return None
        
        model_id = self._extract_model_id(url)
        if not model_id:
            logger.error(f"Could not extract model ID from URL: {url}")
            return None
        
        try:
            # Fetch model info
            api_url = f"{self.HF_API_BASE}/models/{model_id}"
            response = requests.get(
                api_url, 
                headers=self._get_headers(is_github=False),
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"HuggingFace API returned {response.status_code} for {model_id}")
                # Return basic info even if API fails
                return ModelInfo(
                    name=model_id,
                    url=url,
                    api_data={},
                    license="unknown"
                )
            
            data = response.json()
            
            # Try to fetch README
            readme = ""
            try:
                readme_url = f"https://huggingface.co/{model_id}/raw/main/README.md"
                readme_resp = requests.get(readme_url, timeout=10)
                if readme_resp.status_code == 200:
                    readme = readme_resp.text
            except Exception:
                pass
            
            return ModelInfo(
                name=model_id,
                url=url,
                api_data=data,
                downloads=data.get("downloads", 0),
                likes=data.get("likes", 0),
                last_modified=data.get("lastModified", ""),
                tags=data.get("tags", []),
                pipeline_tag=data.get("pipeline_tag", ""),
                library_name=data.get("library_name", ""),
                model_index=data.get("model_index") or data.get("modelIndex") or [],
                license=data.get("license", data.get("cardData", {}).get("license", "")),
                readme=readme,
                siblings=data.get("siblings", [])
            )
            
        except Exception as e:
            logger.error(f"Error fetching model info for {model_id}: {e}")
            return ModelInfo(
                name=model_id,
                url=url,
                api_data={},
                license="unknown"
            )
    
    def parse_dataset_url(self, url: str) -> Optional[DatasetInfo]:
        """Parse HuggingFace dataset URL and fetch metadata"""
        if not requests:
            return None
        
        dataset_id = self._extract_dataset_id(url)
        if not dataset_id:
            logger.error(f"Could not extract dataset ID from URL: {url}")
            return None
        
        try:
            api_url = f"{self.HF_API_BASE}/datasets/{dataset_id}"
            response = requests.get(
                api_url,
                headers=self._get_headers(is_github=False),
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                return DatasetInfo(
                    name=dataset_id,
                    url=url,
                    api_data={},
                    license="unknown"
                )
            
            data = response.json()
            
            return DatasetInfo(
                name=dataset_id,
                url=url,
                api_data=data,
                downloads=data.get("downloads", 0),
                likes=data.get("likes", 0),
                tags=data.get("tags", []),
                license=data.get("license", ""),
                size_bytes=data.get("size", 0)
            )
            
        except Exception as e:
            logger.error(f"Error fetching dataset info: {e}")
            return DatasetInfo(
                name=dataset_id,
                url=url,
                api_data={},
                license="unknown"
            )
    
    def parse_code_url(self, url: str) -> Optional[CodeInfo]:
        """Parse GitHub URL and fetch repository metadata"""
        if not requests:
            return None
        
        owner, repo = self._extract_github_info(url)
        if not owner or not repo:
            logger.error(f"Could not extract owner/repo from URL: {url}")
            return None
        
        try:
            api_url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}"
            response = requests.get(
                api_url,
                headers=self._get_headers(is_github=True),
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                return CodeInfo(
                    name=f"{owner}/{repo}",
                    url=url,
                    api_data={},
                    license="unknown"
                )
            
            data = response.json()
            
            # Get license
            license_info = data.get("license") or {}
            license_name = license_info.get("spdx_id", "unknown") if isinstance(license_info, dict) else "unknown"
            
            return CodeInfo(
                name=f"{owner}/{repo}",
                url=url,
                api_data=data,
                stars=data.get("stargazers_count", 0),
                forks=data.get("forks_count", 0),
                language=data.get("language", ""),
                license=license_name,
                size_kb=data.get("size", 0),
                open_issues=data.get("open_issues_count", 0),
                last_updated=data.get("updated_at", "")
            )
            
        except Exception as e:
            logger.error(f"Error fetching GitHub repo info: {e}")
            return CodeInfo(
                name=f"{owner}/{repo}",
                url=url,
                api_data={},
                license="unknown"
            )
    
    def parse_url(self, url: str) -> Dict[str, Any]:
        """
        Generic URL parser that returns appropriate info based on URL type
        """
        url_type = self.identify_url_type(url)
        
        if url_type == "MODEL":
            info = self.parse_model_url(url)
            return {
                "type": "model",
                "name": info.name if info else "",
                "info": info
            }
        elif url_type == "DATASET":
            info = self.parse_dataset_url(url)
            return {
                "type": "dataset",
                "name": info.name if info else "",
                "info": info
            }
        elif url_type == "CODE":
            info = self.parse_code_url(url)
            return {
                "type": "code",
                "name": info.name if info else "",
                "info": info
            }
        else:
            return {
                "type": "unknown",
                "name": "",
                "info": None
            }
    
    def extract_name_from_url(self, url: str) -> str:
        """Extract and normalize artifact name from URL"""
        url_type = self.identify_url_type(url)
        
        if url_type == "MODEL":
            name = self._extract_model_id(url)
        elif url_type == "DATASET":
            name = self._extract_dataset_id(url)
        elif url_type == "CODE":
            owner, repo = self._extract_github_info(url)
            name = repo if repo else ""
        else:
            # Fallback: extract last path segment
            name = url.rstrip('/').split('/')[-1]
        
        # Normalize: decode URL encoding, lowercase, strip
        name = unquote(name).strip().lower()
        return name
