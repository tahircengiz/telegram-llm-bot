import httpx
import logging
from typing import List, Dict, Any, Optional
from ..schemas import TestResponse

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    """Home Assistant REST API Client"""
    
    def __init__(self, base_url: str, api_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.headers = {}
        
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
        
        self.headers["Content-Type"] = "application/json"
    
    async def test_connection(self) -> TestResponse:
        """Test HA connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/",
                    headers=self.headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return TestResponse(
                        success=True,
                        message="Home Assistant connection successful",
                        details={"message": data.get("message")}
                    )
                else:
                    return TestResponse(
                        success=False,
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return TestResponse(
                success=False,
                message=f"Connection failed: {str(e)}"
            )
    
    async def get_states(self, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get entity states"""
        async with httpx.AsyncClient() as client:
            if entity_id:
                url = f"{self.base_url}/api/states/{entity_id}"
            else:
                url = f"{self.base_url}/api/states"
            
            response = await client.get(url, headers=self.headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                return [data] if entity_id else data
            else:
                raise Exception(f"HA API error: {response.status_code}")
    
    async def call_service(
        self,
        domain: str,
        service: str,
        entity_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call HA service"""
        
        service_data = data or {}
        if entity_id:
            service_data["entity_id"] = entity_id
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self.headers,
                json=service_data,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HA service call failed: {response.status_code}")
    
    async def turn_on(self, entity_id: str) -> Dict[str, Any]:
        """Turn on entity"""
        domain = entity_id.split(".")[0]
        return await self.call_service(domain, "turn_on", entity_id)
    
    async def turn_off(self, entity_id: str) -> Dict[str, Any]:
        """Turn off entity"""
        domain = entity_id.split(".")[0]
        return await self.call_service(domain, "turn_off", entity_id)
    
    async def set_temperature(self, entity_id: str, temperature: float) -> Dict[str, Any]:
        """Set thermostat temperature"""
        return await self.call_service(
            "climate",
            "set_temperature",
            entity_id,
            {"temperature": temperature}
        )
    
    async def get_entities(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all entities, optionally filtered by domain"""
        try:
            states = await self.get_states()
            if domain:
                return [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
            return states
        except Exception as e:
            logger.error(f"Error getting entities: {e}")
            return []
    
    async def search_entities(self, query: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search entities by name/alias (fuzzy search)"""
        entities = await self.get_entities(domain)
        query_lower = query.lower()
        results = []
        
        for entity in entities:
            entity_id = entity.get("entity_id", "")
            attributes = entity.get("attributes", {})
            friendly_name = attributes.get("friendly_name", "")
            
            # Check if query matches entity_id or friendly_name
            if (query_lower in entity_id.lower() or 
                query_lower in friendly_name.lower() or
                any(query_lower in str(v).lower() for v in attributes.values() if isinstance(v, str))):
                results.append(entity)
        
        return results
    
    async def get_services(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available services from Home Assistant"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/services",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get services: {response.status_code}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return {}
    
    async def get_entity_info(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed entity information including state and capabilities"""
        try:
            states = await self.get_states(entity_id)
            if not states or len(states) == 0:
                return None
            
            state = states[0]
            attributes = state.get("attributes", {})
            domain = entity_id.split(".")[0]
            
            return {
                "entity_id": entity_id,
                "domain": domain,
                "state": state.get("state", "unknown"),
                "attributes": attributes,
                "friendly_name": attributes.get("friendly_name", entity_id),
                "supported_features": attributes.get("supported_features", 0),
                "device_class": attributes.get("device_class"),
                "unit_of_measurement": attributes.get("unit_of_measurement"),
            }
        except Exception as e:
            logger.error(f"Error getting entity info for {entity_id}: {e}")
            return None
    
    async def get_entity_state(self, entity_id: str) -> Optional[str]:
        """Get current state of an entity"""
        try:
            info = await self.get_entity_info(entity_id)
            return info.get("state") if info else None
        except Exception as e:
            logger.error(f"Error getting entity state for {entity_id}: {e}")
            return None
