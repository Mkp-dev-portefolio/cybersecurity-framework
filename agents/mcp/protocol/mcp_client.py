"""
Async HTTP client for the MCP (Model Context Protocol) gateway.

Provides tool discovery, tool invocation, audit logging, and health checks
against a running MCP server (e.g. infrastructure/mcp-server).
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from .tool_definitions import ToolDefinition

logger = logging.getLogger(__name__)

# Timeout for regular requests (seconds)
_REQUEST_TIMEOUT = 30
# Timeout for audit log fire-and-forget (seconds)
_AUDIT_TIMEOUT = 5


class MCPClient:
    """
    Async client for interacting with the MCP gateway.

    Usage::

        client = MCPClient(gateway_url="http://mcp-gateway:8811", agent_id="abc123")
        await client.connect()
        tools = await client.get_available_tools()
        result = await client.call_tool("issue_certificate", {"common_name": "svc.local"})
        await client.disconnect()

    The client can also be used as an async context manager::

        async with MCPClient(...) as client:
            tools = await client.get_available_tools()
    """

    def __init__(self, gateway_url: str, agent_id: str):
        """
        Args:
            gateway_url: Base URL of the MCP gateway, e.g. "http://mcp-gateway:8811".
            agent_id: Unique identifier for the calling agent (used in audit logs).
        """
        self.gateway_url = gateway_url.rstrip("/")
        self.agent_id = agent_id
        self._session: Optional[aiohttp.ClientSession] = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open the underlying aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT),
                headers={"X-Agent-ID": self.agent_id},
            )

    async def disconnect(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "MCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> aiohttp.ClientSession:
        """Return the session, opening it lazily if needed."""
        if self._session is None or self._session.closed:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.connect())
        return self._session  # type: ignore[return-value]

    async def _get_session(self) -> aiohttp.ClientSession:
        """Return the session, creating it lazily if not yet open."""
        if self._session is None or self._session.closed:
            await self.connect()
        return self._session  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Verify that the MCP gateway is reachable and healthy.

        Returns:
            True if the gateway reports a healthy status, False otherwise.
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.gateway_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("status") in ("healthy", "ok", True)
                return False
        except Exception as exc:
            logger.warning("MCP health check failed: %s", exc)
            return False

    async def get_available_tools(self) -> List[ToolDefinition]:
        """
        Retrieve the list of tools exposed by the MCP gateway.

        Returns:
            List of :class:`ToolDefinition` objects.

        Raises:
            RuntimeError: If the gateway returns a non-200 response.
        """
        session = await self._get_session()
        try:
            async with session.post(f"{self.gateway_url}/mcp/tools/list") as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(
                        f"MCP gateway returned {resp.status} for tools/list: {text}"
                    )
                data = await resp.json()
        except aiohttp.ClientError as exc:
            raise RuntimeError(f"Failed to reach MCP gateway at {self.gateway_url}: {exc}") from exc

        tools: List[ToolDefinition] = []
        for item in data.get("tools", []):
            tools.append(
                ToolDefinition(
                    name=item["name"],
                    description=item.get("description", ""),
                    input_schema=item.get("input_schema", item.get("inputSchema", {})),
                    category=item.get("category"),
                    security_level=item.get("security_level"),
                )
            )
        logger.debug("Discovered %d MCP tools from %s", len(tools), self.gateway_url)
        return tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Invoke a named tool on the MCP gateway.

        Args:
            name: The tool name (must match a value returned by :meth:`get_available_tools`).
            arguments: Keyword arguments forwarded to the tool.

        Returns:
            The tool result (parsed from JSON response).

        Raises:
            RuntimeError: If the gateway returns an error response.
        """
        session = await self._get_session()
        payload = {"name": name, "arguments": arguments}
        try:
            async with session.post(
                f"{self.gateway_url}/mcp/tools/call", json=payload
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(
                        f"MCP tool '{name}' returned {resp.status}: {text}"
                    )
                result = await resp.json()
        except aiohttp.ClientError as exc:
            raise RuntimeError(
                f"Failed to call MCP tool '{name}' at {self.gateway_url}: {exc}"
            ) from exc

        # Unwrap standard MCP result envelope {"success": bool, "data": ..., "error": ...}
        if isinstance(result, dict) and "success" in result:
            if not result["success"]:
                raise RuntimeError(
                    f"MCP tool '{name}' reported failure: {result.get('error', 'unknown error')}"
                )
            return result.get("data", result)

        return result

    async def send_audit_log(self, entry: Dict[str, Any]) -> None:
        """
        Send a security audit log entry to the MCP gateway (fire-and-forget).

        Failures are logged as warnings and never re-raised so that audit
        logging does not interrupt normal agent execution.

        Args:
            entry: Audit log payload dict.
        """
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.gateway_url}/audit/log",
                json=entry,
                timeout=aiohttp.ClientTimeout(total=_AUDIT_TIMEOUT),
            ) as resp:
                if resp.status not in (200, 201, 202, 204):
                    text = await resp.text()
                    logger.warning(
                        "Audit log POST returned %d for agent %s: %s",
                        resp.status,
                        self.agent_id,
                        text,
                    )
        except Exception as exc:
            logger.warning(
                "Failed to send audit log for agent %s: %s", self.agent_id, exc
            )
