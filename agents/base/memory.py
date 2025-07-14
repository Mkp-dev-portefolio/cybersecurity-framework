"""
Agent Memory Management
"""

from typing import List, Dict, Any, Optional
from collections import deque
from datetime import datetime
import logging


class AgentMemory:
    """Simple agent memory store"""

    def __init__(self, max_size: int, agent_id: str):
        self.max_size = max_size
        self.agent_id = agent_id
        self.memory = deque(maxlen=max_size)
        self.logger = logging.getLogger(__name__)

    async def store_interaction(self, interaction: Dict[str, Any]):
        """Store an interaction in memory"""
        if len(self.memory) >= self.max_size:
            self.memory.popleft()
        self.memory.append({"timestamp": datetime.now(), **interaction})
        self.logger.info(f"Stored interaction in memory. Current size: {len(self.memory)}")

    async def get_recent_interactions(self, count: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent interactions from memory"""
        return list(self.memory)[-count:]

    async def clear_memory(self):
        """Clear all stored interactions"""
        self.memory.clear()
        self.logger.info("Cleared memory.")

    async def health_check(self) -> bool:
        """Perform a health check on memory"""
        # Here we could add more complex memory diagnostics
        healthy = len(self.memory) <= self.max_size
        self.logger.info(f"Memory health check: {'healthy' if healthy else 'unhealthy'}")
        return healthy

    async def cleanup(self):
        """Cleanup memory resources"""
        await self.clear_memory()

    async def get_size(self) -> int:
        """Get the current memory size"""
        return len(self.memory)
