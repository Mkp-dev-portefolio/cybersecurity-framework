"""
MCP Protocol Implementation
Model Context Protocol for PKI operations
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MCPTool:
    """MCP Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
                "required": list(self.parameters.keys())
            }
        }


@dataclass
class MCPResult:
    """MCP operation result"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "success": self.success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
            
        return result


class MCPServer:
    """MCP Server implementation"""
    
    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, MCPTool] = {}
        self.session_id = str(uuid.uuid4())
        
    def register_tool(self, tool: MCPTool):
        """Register a new tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered MCP tool: {tool.name}")
        
    def initialize(self) -> Dict[str, Any]:
        """Initialize MCP session"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": self.name,
                "version": "1.0.0"
            },
            "sessionId": self.session_id
        }
        
    def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": [tool.to_dict() for tool in self.tools.values()]
        }
        
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        try:
            if tool_name not in self.tools:
                return MCPResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found"
                ).to_dict()
                
            tool = self.tools[tool_name]
            
            # Validate parameters
            missing_params = []
            for param_name, param_def in tool.parameters.items():
                if param_name not in parameters and param_def.get("required", True):
                    missing_params.append(param_name)
                    
            if missing_params:
                return MCPResult(
                    success=False,
                    error=f"Missing required parameters: {', '.join(missing_params)}"
                ).to_dict()
            
            # Call the tool handler
            result = await tool.handler(**parameters)
            
            if isinstance(result, MCPResult):
                return result.to_dict()
            else:
                return MCPResult(success=True, data=result).to_dict()
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}", error=str(e))
            return MCPResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            ).to_dict()


class MCPClient:
    """MCP Client implementation"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session = None
        self.session_id = None
        self.available_tools = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self):
        """Connect to MCP server"""
        import aiohttp
        
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Initialize session
            async with self.session.post(
                f"{self.server_url}/mcp/initialize"
            ) as response:
                if response.status == 200:
                    init_data = await response.json()
                    self.session_id = init_data.get("sessionId")
                    
            # Get available tools
            await self.refresh_tools()
            
            logger.info(f"Connected to MCP server: {self.server_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server", error=str(e))
            raise
            
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.session:
            await self.session.close()
            
    async def refresh_tools(self):
        """Refresh available tools from server"""
        try:
            async with self.session.post(
                f"{self.server_url}/mcp/tools/list"
            ) as response:
                if response.status == 200:
                    tools_data = await response.json()
                    self.available_tools = {
                        tool["name"]: tool for tool in tools_data.get("tools", [])
                    }
                    
        except Exception as e:
            logger.error("Failed to refresh tools", error=str(e))
            
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the server"""
        try:
            async with self.session.post(
                f"{self.server_url}/mcp/tools/call",
                json={
                    "tool_name": tool_name,
                    "parameters": parameters
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return MCPResult(
                        success=False,
                        error=f"Server error: {error_text}"
                    ).to_dict()
                    
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}", error=str(e))
            return MCPResult(
                success=False,
                error=f"Client error: {str(e)}"
            ).to_dict()
            
    def get_available_tools(self) -> Dict[str, Any]:
        """Get list of available tools"""
        return self.available_tools
        
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        return self.available_tools.get(tool_name)
