"""
Tool definition dataclasses for the MCP protocol.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolDefinition:
    """
    Describes a tool available through the MCP gateway.

    Attributes:
        name: Unique tool identifier used when calling the tool.
        description: Human-readable description of what the tool does.
        input_schema: JSON-schema-style dict describing the expected inputs,
            e.g. {"type": "object", "properties": {...}, "required": [...]}.
    """

    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)

    # Optional metadata returned by some MCP servers
    category: Optional[str] = None
    security_level: Optional[str] = None
