"""
DynamoDB Database Connection Layer
"""
import os
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

from .config import get_settings

logger = logging.getLogger(__name__)


class DynamoDBManager:
    """Manager for DynamoDB operations"""
    
    def __init__(self):
        settings = get_settings()
        self.table_name = settings.dynamodb_table_name
        
        # Configure DynamoDB client
        config = {
            "region_name": settings.aws_region
        }
        
        if settings.dynamodb_endpoint_url:
            config["endpoint_url"] = settings.dynamodb_endpoint_url
        
        self.dynamodb = boto3.resource("dynamodb", **config)
        self.table = self.dynamodb.Table(self.table_name)
    
    def get_table(self):
        """Get the DynamoDB table"""
        return self.table
    
    # ============ ARTIFACT OPERATIONS ============
    
    def create_artifact(self, artifact_type: str, artifact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new artifact"""
        pk = f"{artifact_type}#{artifact_id}"
        
        item = {
            "pk": pk,
            "sk": "METADATA",
            "id": artifact_id,
            "type": artifact_type,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            **self._convert_floats_to_decimal(data)
        }
        
        self.table.put_item(Item=item)
        return item
    
    def get_artifact(self, artifact_type: str, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get a single artifact by type and ID"""
        pk = f"{artifact_type}#{artifact_id}"
        
        response = self.table.get_item(Key={"pk": pk, "sk": "METADATA"})
        
        if "Item" in response:
            return self._convert_decimals_to_floats(response["Item"])
        return None
    
    def update_artifact(self, artifact_type: str, artifact_id: str, updates: Dict[str, Any]) -> bool:
        """Update an artifact"""
        pk = f"{artifact_type}#{artifact_id}"
        
        # Check exists
        existing = self.get_artifact(artifact_type, artifact_id)
        if not existing:
            return False
        
        # Build update expression
        update_parts = ["updatedAt = :ts"]
        values = {":ts": datetime.now(timezone.utc).isoformat()}
        names = {}
        
        for key, value in updates.items():
            if key not in ("pk", "sk", "id", "type", "createdAt"):
                safe_key = f"#{key}"
                names[safe_key] = key
                values[f":{key}"] = self._convert_floats_to_decimal(value) if isinstance(value, (dict, list)) else (Decimal(str(value)) if isinstance(value, float) else value)
                update_parts.append(f"{safe_key} = :{key}")
        
        self.table.update_item(
            Key={"pk": pk, "sk": "METADATA"},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeValues=values,
            ExpressionAttributeNames=names if names else None
        )
        
        return True
    
    def delete_artifact(self, artifact_type: str, artifact_id: str) -> bool:
        """Delete an artifact and related items"""
        pk = f"{artifact_type}#{artifact_id}"
        
        # Check exists
        existing = self.get_artifact(artifact_type, artifact_id)
        if not existing:
            return False
        
        # Delete metadata
        self.table.delete_item(Key={"pk": pk, "sk": "METADATA"})
        
        # Delete related ratings
        ratings = self.table.query(
            KeyConditionExpression=Key("pk").eq(pk) & Key("sk").begins_with("RATING#")
        )
        
        with self.table.batch_writer() as batch:
            for item in ratings.get("Items", []):
                batch.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
        
        return True
    
    def list_artifacts(self, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all artifacts, optionally filtered by type"""
        filter_expr = "sk = :sk"
        values = {":sk": "METADATA"}
        
        if filter_type:
            filter_expr += " AND begins_with(pk, :type)"
            values[":type"] = f"{filter_type}#"
        
        response = self.table.scan(
            FilterExpression=filter_expr,
            ExpressionAttributeValues=values
        )
        
        items = response.get("Items", [])
        
        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = self.table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeValues=values,
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))
        
        return [self._convert_decimals_to_floats(item) for item in items]
    
    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find artifacts by name"""
        normalized_name = name.lower().strip()
        
        response = self.table.scan(
            FilterExpression="#n = :name AND sk = :sk",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={":name": normalized_name, ":sk": "METADATA"}
        )
        
        return [self._convert_decimals_to_floats(item) for item in response.get("Items", [])]
    
    def find_by_regex(self, pattern: str) -> List[Dict[str, Any]]:
        """Find artifacts matching a regex pattern"""
        import re
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return []
        
        all_items = self.list_artifacts()
        
        return [
            item for item in all_items
            if regex.search(item.get("name", ""))
        ]
    
    # ============ RATING OPERATIONS ============
    
    def save_rating(self, artifact_type: str, artifact_id: str, rating_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a rating for an artifact"""
        pk = f"{artifact_type}#{artifact_id}"
        ts = datetime.now(timezone.utc).isoformat()
        
        item = {
            "pk": pk,
            "sk": f"RATING#{ts}",
            "createdAt": ts,
            **self._convert_floats_to_decimal(rating_data)
        }
        
        self.table.put_item(Item=item)
        return self._convert_decimals_to_floats(item)
    
    def get_latest_rating(self, artifact_type: str, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent rating for an artifact"""
        pk = f"{artifact_type}#{artifact_id}"
        
        response = self.table.query(
            KeyConditionExpression=Key("pk").eq(pk) & Key("sk").begins_with("RATING#"),
            ScanIndexForward=False,  # Descending order
            Limit=1
        )
        
        items = response.get("Items", [])
        if items:
            return self._convert_decimals_to_floats(items[0])
        return None
    
    # ============ CONFIG OPERATIONS ============
    
    def get_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """Get a config value"""
        response = self.table.get_item(Key={"pk": "CONFIG", "sk": config_key})
        
        if "Item" in response:
            return self._convert_decimals_to_floats(response["Item"])
        return None
    
    def set_config(self, config_key: str, data: Dict[str, Any]) -> None:
        """Set a config value"""
        item = {
            "pk": "CONFIG",
            "sk": config_key,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            **self._convert_floats_to_decimal(data)
        }
        self.table.put_item(Item=item)
    
    # ============ RESET ============
    
    def reset_all(self) -> int:
        """Delete all items from the table"""
        deleted = 0
        last_key = None
        
        while True:
            scan_kwargs = {}
            if last_key:
                scan_kwargs["ExclusiveStartKey"] = last_key
            
            response = self.table.scan(**scan_kwargs)
            items = response.get("Items", [])
            
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
                    deleted += 1
            
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
        
        # Reinitialize default config
        self.set_config("TRACKS", {"tracks": []})
        
        return deleted
    
    # ============ HELPERS ============
    
    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert floats to Decimal for DynamoDB"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        return obj
    
    def _convert_decimals_to_floats(self, obj: Any) -> Any:
        """Convert Decimals back to floats"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals_to_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_floats(item) for item in obj]
        return obj


# Global instance
_db_manager: Optional[DynamoDBManager] = None


def get_db() -> DynamoDBManager:
    """Get the database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DynamoDBManager()
    return _db_manager
