"""
AWS Lambda Handler for Trustworthy Model Registry API
This is the entry point for AWS Lambda - delegates to the api module
"""
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_root)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the handler from the api module
from api.main import handler as api_handler, route_request

# Re-export for Lambda
def lambda_handler(event, context):
    """AWS Lambda entry point"""
    return api_handler(event, context)


# Also export as 'handler' for SAM template compatibility
handler = lambda_handler
