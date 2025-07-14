"""
Tool Registry for managing agent tools with MCP integration
"""

from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from datetime import datetime
import logging

from smolagents.tools import Tool as SmolagentsTool


@dataclass
class ToolMetadata:
    """Metadata for registered tools"""
    name: str
    description: str
    category: str
    version: str = "1.0.0"
    author: str = "system"
    security_level: str = "standard"
    mcp_enabled: bool = False
    registered_at: datetime = None
    usage_count: int = 0
    last_used: Optional[datetime] = None


class ToolRegistry:
    """Registry for managing agent tools"""
    
    def __init__(self):
        self.tools: Dict[str, SmolagentsTool] = {}
        self.metadata: Dict[str, ToolMetadata] = {}
        self.categories: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_tool(
        self,
        tool: SmolagentsTool,
        category: str = "general",
        security_level: str = "standard",
        mcp_enabled: bool = False
    ):
        """Register a tool with metadata"""
        if not isinstance(tool, SmolagentsTool):
            raise ValueError("Tool must be a SmolagentsTool instance")
        
        metadata = ToolMetadata(
            name=tool.name,
            description=tool.description,
            category=category,
            security_level=security_level,
            mcp_enabled=mcp_enabled,
            registered_at=datetime.now()
        )
        
        self.tools[tool.name] = tool
        self.metadata[tool.name] = metadata
        
        # Update category index
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(tool.name)
        
        self.logger.info(f"Registered tool: {tool.name} (category: {category})")
    
    def get_tool(self, name: str) -> Optional[SmolagentsTool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_tools_by_category(self, category: str) -> List[SmolagentsTool]:
        """Get all tools in a category"""
        tool_names = self.categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def get_all_tools(self) -> List[SmolagentsTool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def get_tool_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata"""
        return self.metadata.get(name)
    
    def update_usage(self, name: str):
        """Update tool usage statistics"""
        if name in self.metadata:
            self.metadata[name].usage_count += 1
            self.metadata[name].last_used = datetime.now()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_tools": len(self.tools),
            "categories": {cat: len(tools) for cat, tools in self.categories.items()},
            "most_used": sorted(
                [(name, meta.usage_count) for name, meta in self.metadata.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool"""
        if name in self.tools:
            tool = self.tools.pop(name)
            metadata = self.metadata.pop(name)
            
            # Update category index
            if metadata.category in self.categories:
                self.categories[metadata.category].remove(name)
                if not self.categories[metadata.category]:
                    del self.categories[metadata.category]
            
            self.logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools with their metadata"""
        return [
            {
                "name": name,
                "description": tool.description,
                "category": self.metadata[name].category,
                "security_level": self.metadata[name].security_level,
                "mcp_enabled": self.metadata[name].mcp_enabled,
                "usage_count": self.metadata[name].usage_count,
                "last_used": self.metadata[name].last_used.isoformat() if self.metadata[name].last_used else None
            }
            for name, tool in self.tools.items()
        ]
