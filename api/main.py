"""
FastAPI Main Application with Lambda Handler
"""
import json
import re
import logging
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import route handlers
from api.routes.health import health_check, health_components
from api.routes.auth import authenticate, login, verify_auth
from api.routes.tracks import get_tracks
from api.routes.artifacts import (
    create_artifact, get_artifact, update_artifact, delete_artifact,
    list_artifacts, get_artifact_by_name, get_artifact_by_regex,
    reset_registry, ingest_model
)
from api.routes.rating import rate_model
from api.routes.cost import get_artifact_cost
from api.routes.lineage import get_artifact_lineage
from api.routes.license_check import check_license


# ============================================================
# RESPONSE HELPERS
# ============================================================

def json_response(status_code: int, body: Any, headers: Optional[Dict[str, str]] = None) -> Dict:
    """Create a JSON response"""
    h = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
    }
    if headers:
        h.update(headers)
    
    return {
        "statusCode": status_code,
        "body": json.dumps(body) if not isinstance(body, str) else body,
        "headers": h
    }


def text_response(status_code: int, body: str, headers: Optional[Dict[str, str]] = None) -> Dict:
    """Create a text response"""
    h = {
        "Content-Type": "text/plain",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*"
    }
    if headers:
        h.update(headers)
    
    return {
        "statusCode": status_code,
        "body": body,
        "headers": h
    }


def error_response(status_code: int, message: str) -> Dict:
    """Create an error response"""
    return json_response(status_code, {"error": message})


# ============================================================
# LAMBDA HANDLER
# ============================================================

def handler(event: Dict, context: Any) -> Dict:
    """
    AWS Lambda handler for the API
    Supports both HTTP API (v2) and REST API (v1) event formats
    """
    try:
        # Extract HTTP method
        method = (
            event.get("httpMethod") or
            event.get("requestContext", {}).get("http", {}).get("method", "")
        ).upper()
        
        # Extract path
        path = (
            event.get("path") or
            event.get("rawPath") or
            event.get("requestContext", {}).get("http", {}).get("path", "")
        )
        
        # Strip stage prefix (e.g., /prod, /dev)
        if path.startswith("/prod"):
            path = path[5:] or "/"
        elif path.startswith("/dev"):
            path = path[4:] or "/"
        
        # Extract headers (normalize to lowercase keys)
        raw_headers = event.get("headers") or {}
        headers = {k: v for k, v in raw_headers.items()}
        
        # Extract query parameters
        query_params = event.get("queryStringParameters") or {}
        
        # Extract and parse body
        body = None
        raw_body = event.get("body")
        
        if raw_body:
            # Handle base64 encoding
            if event.get("isBase64Encoded"):
                import base64
                raw_body = base64.b64decode(raw_body).decode("utf-8")
            
            try:
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                pass  # Body is not JSON
        
        # Route the request
        return route_request(method, path, headers, body, query_params)
        
    except Exception as e:
        logger.exception("Unhandled exception in handler")
        return error_response(500, f"Internal server error: {str(e)}")


def route_request(method: str, path: str, headers: Dict, body: Any, query_params: Dict) -> Dict:
    """Route the request to the appropriate handler"""
    
    # ========== CORS PREFLIGHT ==========
    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Authorization",
                "Access-Control-Max-Age": "86400"
            },
            "body": ""
        }
    
    # ========== HEALTH (NO AUTH) ==========
    if path == "/health" and method == "GET":
        return json_response(200, health_check())
    
    if path == "/health/components" and method == "GET":
        window = int(query_params.get("windowMinutes", 60))
        timeline = query_params.get("includeTimeline", "false").lower() == "true"
        return json_response(200, health_components(window, timeline))
    
    # ========== TRACKS (NO AUTH) ==========
    if path == "/tracks" and method == "GET":
        return json_response(200, get_tracks())
    
    # ========== LOGIN (NO AUTH) ==========
    if path == "/login" and method in ("GET", "POST"):
        status, result = login(body)
        if status == 200:
            return text_response(status, result)
        return text_response(status, result)
    
    # ========== AUTHENTICATE (NO AUTH) ==========
    if path == "/authenticate" and method == "PUT":
        status, result = authenticate(body)
        if status == 200:
            return text_response(status, result)
        return text_response(status, result)
    
    # ========== RESET (AUTH REQUIRED) ==========
    if path == "/reset" and method in ("DELETE", "POST"):
        if not verify_auth(headers):
            return error_response(403, "Authentication failed")
        status, result = reset_registry()
        return json_response(status, result)
    
    # ========== ALL ROUTES BELOW REQUIRE AUTH ==========
    if not verify_auth(headers):
        return error_response(403, "Authentication failed")
    
    # ========== MODEL INGEST ==========
    if path == "/artifact/model/ingest" and method == "POST":
        status, result = ingest_model(body)
        return json_response(status, result)
    
    if path in ("/artifact/dataset/ingest", "/artifact/code/ingest") and method == "POST":
        artifact_type = path.split("/")[2]
        status, result = create_artifact(artifact_type, body)
        return json_response(status, result)
    
    # ========== CREATE ARTIFACT ==========
    create_match = re.match(r"^/artifact/(model|dataset|code)$", path)
    if create_match and method == "POST":
        artifact_type = create_match.group(1)
        status, result = create_artifact(artifact_type, body)
        return json_response(status, result)
    
    # ========== RATING ==========
    rate_match = re.match(r"^/artifact/model/([^/]+)/rate$", path)
    if rate_match and method == "GET":
        artifact_id = rate_match.group(1)
        status, result = rate_model(artifact_id)
        return json_response(status, result)
    
    # ========== COST ==========
    cost_match = re.match(r"^/artifact/(model|dataset|code)/([^/]+)/cost$", path)
    if cost_match and method == "GET":
        artifact_type = cost_match.group(1)
        artifact_id = cost_match.group(2)
        include_dep = query_params.get("dependency", "false").lower() == "true"
        status, result = get_artifact_cost(artifact_type, artifact_id, include_dep)
        return json_response(status, result)
    
    # ========== LINEAGE ==========
    lineage_match = re.match(r"^/artifact/model/([^/]+)/lineage$", path)
    if lineage_match and method == "GET":
        artifact_id = lineage_match.group(1)
        status, result = get_artifact_lineage(artifact_id)
        return json_response(status, result)
    
    # ========== LICENSE CHECK ==========
    license_match = re.match(r"^/artifact/model/([^/]+)/license-check$", path)
    if license_match and method == "POST":
        artifact_id = license_match.group(1)
        status, result = check_license(artifact_id, body)
        return json_response(status, result)
    
    # ========== ARTIFACT CRUD ==========
    detail_match = re.match(r"^/artifact/(model|dataset|code)/([^/]+)$", path)
    if detail_match:
        artifact_type = detail_match.group(1)
        artifact_id = detail_match.group(2)
        
        if method == "GET":
            status, result = get_artifact(artifact_type, artifact_id)
            return json_response(status, result)
        
        if method == "PUT":
            status, result = update_artifact(artifact_type, artifact_id, body)
            return json_response(status, result)
        
        if method == "DELETE":
            status, result = delete_artifact(artifact_type, artifact_id)
            return json_response(status, result)
    
    # ========== FIND BY NAME ==========
    name_match = re.match(r"^/artifact/byName/(.+)$", path)
    if name_match and method == "GET":
        name = name_match.group(1)
        status, result = get_artifact_by_name(name)
        return json_response(status, result)
    
    # ========== FIND BY REGEX ==========
    if path == "/artifact/byRegEx" and method == "POST":
        status, result = get_artifact_by_regex(body)
        return json_response(status, result)
    
    # ========== LIST ARTIFACTS ==========
    if path == "/artifacts":
        if method == "GET":
            queries = [{"name": "*"}]
        elif method == "POST":
            queries = body if isinstance(body, list) else [body] if body else [{"name": "*"}]
        else:
            return error_response(405, "Method not allowed")
        
        offset = query_params.get("offset", "0")
        status, result, extra_headers = list_artifacts(queries, offset)
        return json_response(status, result, extra_headers)
    
    # ========== AUDIT (placeholder) ==========
    audit_match = re.match(r"^/artifact/(model|dataset|code)/([^/]+)/audit$", path)
    if audit_match and method == "GET":
        artifact_type = audit_match.group(1)
        artifact_id = audit_match.group(2)
        
        from api.database import get_db
        db = get_db()
        artifact = db.get_artifact(artifact_type, artifact_id)
        
        if not artifact:
            return error_response(404, "Artifact not found")
        
        # Return empty audit trail (placeholder)
        return json_response(200, [])
    
    # ========== 404 ==========
    return error_response(404, f"Endpoint not found: {method} {path}")


# For local testing with uvicorn
try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Trustworthy Model Registry", version="1.0.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def catch_all(request: Request, path: str):
        """Catch-all route that delegates to the Lambda handler"""
        body = None
        try:
            body = await request.json()
        except:
            pass
        
        event = {
            "httpMethod": request.method,
            "path": f"/{path}",
            "headers": dict(request.headers),
            "queryStringParameters": dict(request.query_params),
            "body": json.dumps(body) if body else None
        }
        
        response = handler(event, None)
        
        from fastapi.responses import Response
        return Response(
            content=response["body"],
            status_code=response["statusCode"],
            headers=response.get("headers", {})
        )

except ImportError:
    # FastAPI not available, Lambda-only mode
    app = None
