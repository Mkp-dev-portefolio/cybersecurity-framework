"""
Enhanced Base Agent with smolagents integration and Docker compose-for-agents architecture
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from datetime import datetime
import uuid

from smolagents import Agent, Tool, CodeAgent
from smolagents.tools import Tool as SmolagentsTool
from smolagents.memory import Memory as SmolagentsMemory

from .tool_registry import ToolRegistry
from .memory import AgentMemory
from ..mcp.protocol.mcp_client import MCPClient
from ..mcp.protocol.tool_definitions import ToolDefinition


@dataclass
class AgentConfig:
    """Agent configuration"""
    name: str
    description: str
    model_provider: str = "openai"
    model_name: str = "gpt-4"
    max_iterations: int = 10
    memory_size: int = 1000
    enable_code_execution: bool = False
    mcp_gateway_url: str = "http://mcp-gateway:8811"
    container_id: Optional[str] = None
    security_level: str = "standard"  # standard, high, critical


class CybersecurityAgent(Agent, ABC):
    """
    Enhanced base agent combining smolagents capabilities with MCP protocol
    and Docker compose-for-agents architecture
    """
    
    def __init__(
        self,
        config: AgentConfig,
        tools: Optional[List[Union[Tool, SmolagentsTool]]] = None,
        memory: Optional[Union[AgentMemory, SmolagentsMemory]] = None
    ):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now()
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        
        # Initialize memory system
        self.memory = memory or AgentMemory(
            max_size=config.memory_size,
            agent_id=self.agent_id
        )
        
        # Initialize MCP client
        self.mcp_client = MCPClient(
            gateway_url=config.mcp_gateway_url,
            agent_id=self.agent_id
        )
        
        # Initialize smolagents Agent
        super().__init__(
            name=config.name,
            description=config.description,
            model=self._get_model(),
            tools=tools or [],
            memory=self.memory if isinstance(self.memory, SmolagentsMemory) else None
        )
        
        # Security context
        self.security_context = {
            "level": config.security_level,
            "permissions": self._get_permissions(),
            "audit_enabled": True
        }
        
        self.logger.info(f"Agent {self.config.name} initialized", extra={
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "security_level": config.security_level
        })
    
    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging for the agent"""
        logger = logging.getLogger(f"cybersec_agent.{self.config.name}")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _get_model(self):
        """Get the appropriate model based on configuration"""
        if self.config.model_provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=self._get_api_key())
        elif self.config.model_provider == "docker":
            # Use Docker Model Runner
            return self._get_docker_model()
        else:
            raise ValueError(f"Unsupported model provider: {self.config.model_provider}")
    
    def _get_api_key(self) -> str:
        """Get API key from Docker secrets or environment"""
        import os
        
        # Try Docker secrets first
        secret_path = "/run/secrets/openai-api-key"
        if os.path.exists(secret_path):
            with open(secret_path, 'r') as f:
                return f.read().strip()
        
        # Fallback to environment variable
        return os.getenv("OPENAI_API_KEY", "")
    
    def _get_docker_model(self):
        """Get Docker Model Runner configuration"""
        import os
        base_url = os.getenv("MODEL_RUNNER_URL", "http://model-runner:8080")
        model_name = os.getenv("MODEL_RUNNER_MODEL", "qwen3")
        
        from openai import OpenAI
        return OpenAI(
            base_url=base_url,
            api_key="cannot_be_empty"  # DMR doesn't need real API key
        )
    
    def _get_permissions(self) -> List[str]:
        """Get agent permissions based on security level"""
        permissions = ["read", "execute_tools"]
        
        if self.config.security_level == "high":
            permissions.extend(["write", "modify_config"])
        elif self.config.security_level == "critical":
            permissions.extend(["write", "modify_config", "admin", "security_audit"])
        
        return permissions
    
    async def initialize_tools(self):
        """Initialize and register agent tools"""
        # Register domain-specific tools
        domain_tools = await self._get_domain_tools()
        for tool in domain_tools:
            self.tool_registry.register_tool(tool)
        
        # Register MCP tools
        mcp_tools = await self.mcp_client.get_available_tools()
        for tool_def in mcp_tools:
            mcp_tool = self._create_mcp_tool(tool_def)
            self.tool_registry.register_tool(mcp_tool)
        
        # Update smolagents tools
        self.tools = list(self.tool_registry.get_all_tools())
        
        self.logger.info(f"Initialized {len(self.tools)} tools")
    
    def _create_mcp_tool(self, tool_def: ToolDefinition) -> Tool:
        """Create a smolagents Tool from MCP tool definition"""
        
        class MCPTool(Tool):
            def __init__(self, tool_def: ToolDefinition, mcp_client: MCPClient):
                self.tool_def = tool_def
                self.mcp_client = mcp_client
                super().__init__(
                    name=tool_def.name,
                    description=tool_def.description,
                    inputs=tool_def.input_schema
                )
            
            async def forward(self, **kwargs) -> Any:
                return await self.mcp_client.call_tool(
                    self.tool_def.name,
                    kwargs
                )
        
        return MCPTool(tool_def, self.mcp_client)
    
    @abstractmethod
    async def _get_domain_tools(self) -> List[Tool]:
        """Get domain-specific tools for the agent"""
        pass
    
    async def run_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a task using the agent's capabilities
        
        Args:
            task: The task description
            context: Optional context information
            
        Returns:
            Task execution result
        """
        start_time = datetime.now()
        
        # Log task start
        self.logger.info(f"Starting task: {task[:100]}...", extra={
            "task_id": str(uuid.uuid4()),
            "agent_id": self.agent_id,
            "session_id": self.session_id
        })
        
        try:
            # Store task in memory
            await self.memory.store_interaction({
                "type": "task_start",
                "task": task,
                "context": context,
                "timestamp": start_time.isoformat()
            })
            
            # Execute task using smolagents
            result = await self._execute_task(task, context)
            
            # Store result in memory
            await self.memory.store_interaction({
                "type": "task_complete",
                "task": task,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "duration": (datetime.now() - start_time).total_seconds()
            })
            
            # Security audit log
            if self.security_context["audit_enabled"]:
                await self._audit_log("task_execution", {
                    "task": task,
                    "result_summary": str(result)[:200],
                    "success": True
                })
            
            return {
                "success": True,
                "result": result,
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}", extra={
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "error": str(e)
            })
            
            # Security audit log for failures
            if self.security_context["audit_enabled"]:
                await self._audit_log("task_execution_failed", {
                    "task": task,
                    "error": str(e),
                    "success": False
                })
            
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    async def _execute_task(self, task: str, context: Optional[Dict] = None) -> Any:
        """Execute the task using smolagents capabilities"""
        # Use smolagents run method
        return await self.run(task, context or {})
    
    async def _audit_log(self, event_type: str, data: Dict[str, Any]):
        """Log security audit events"""
        audit_entry = {
            "event_type": event_type,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "security_level": self.security_context["level"]
        }
        
        # Send to MCP gateway for centralized logging
        await self.mcp_client.send_audit_log(audit_entry)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "security_level": self.security_context["level"],
            "tools_count": len(self.tools),
            "memory_size": await self.memory.get_size(),
            "container_id": self.config.container_id
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Check MCP connectivity
            mcp_healthy = await self.mcp_client.health_check()
            
            # Check memory system
            memory_healthy = await self.memory.health_check()
            
            # Check tools
            tools_healthy = len(self.tools) > 0
            
            overall_healthy = mcp_healthy and memory_healthy and tools_healthy
            
            return {
                "healthy": overall_healthy,
                "mcp_gateway": mcp_healthy,
                "memory": memory_healthy,
                "tools": tools_healthy,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            await self.mcp_client.disconnect()
            await self.memory.cleanup()
            self.logger.info("Agent cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
