"""
Entity cache for Home Assistant entities
Caches entity list to avoid frequent API calls
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EntityCache:
    """Cache for Home Assistant entities"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self.cache: Optional[List[Dict[str, Any]]] = None
        self.cache_time: Optional[datetime] = None
        self.ttl_seconds = ttl_seconds
    
    def is_valid(self) -> bool:
        """Check if cache is still valid"""
        if self.cache is None or self.cache_time is None:
            return False
        
        age = (datetime.now() - self.cache_time).total_seconds()
        return age < self.ttl_seconds
    
    def get(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached entities"""
        if self.is_valid():
            return self.cache
        return None
    
    def set(self, entities: List[Dict[str, Any]]):
        """Set cached entities"""
        self.cache = entities
        self.cache_time = datetime.now()
        logger.info(f"Cached {len(entities)} entities")
    
    def clear(self):
        """Clear cache"""
        self.cache = None
        self.cache_time = None
    
    def get_entity_list_for_prompt(self, domain: Optional[str] = None) -> str:
        """Get formatted entity list for LLM prompt"""
        if not self.is_valid() or not self.cache:
            return "Entity list not available"
        
        entities = self.cache
        if domain:
            entities = [e for e in entities if e.get("entity_id", "").startswith(f"{domain}.")]
        
        # Format: entity_id (friendly_name)
        formatted = []
        for entity in entities[:100]:  # Limit to 100 entities
            entity_id = entity.get("entity_id", "")
            friendly_name = entity.get("attributes", {}).get("friendly_name", "")
            if friendly_name:
                formatted.append(f"{entity_id} ({friendly_name})")
            else:
                formatted.append(entity_id)
        
        return "\n".join(formatted) if formatted else "No entities found"


# Global cache instance
_entity_cache: Optional[EntityCache] = None


def get_entity_cache() -> EntityCache:
    """Get global entity cache instance"""
    global _entity_cache
    if _entity_cache is None:
        _entity_cache = EntityCache()
    return _entity_cache
