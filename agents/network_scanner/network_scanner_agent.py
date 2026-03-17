"""
Network Scanner Agent — standalone demonstration agent.

Shows how to build a simple cybersecurity tool that does NOT require the full
CybersecurityAgent / MCP stack, useful for local testing and demos.
"""

import json
import socket
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional


class NetworkScannerAgent:
    """
    A simple network scanning agent that demonstrates the framework.

    This agent can:
    - Check if a host is reachable via ping
    - Scan open ports on a target host
    - Perform basic network reconnaissance
    - Maintain a history of previous scans
    """

    def __init__(self, name: str = "NetworkScanner", config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.description = "Network scanning and reconnaissance agent"
        self.version = "1.0.0"

        # Simple in-memory store (replaces the old broken memory system)
        self._context: Dict[str, Any] = {"scan_history": []}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()

    def _extract_ping_time(self, ping_output: str) -> str:
        """Extract round-trip time from ping command output."""
        for line in ping_output.split("\n"):
            if "time=" in line:
                return line.split("time=")[1].split()[0]
        return "unknown"

    def _assess_risk_level(self, port_scan: Optional[Dict[str, Any]]) -> str:
        """Assess risk level based on open ports."""
        if not port_scan:
            return "unknown"

        open_ports = port_scan.get("open_ports", [])
        high_risk_ports = {21, 23, 135, 139, 445, 1433, 3389}

        if any(p in open_ports for p in high_risk_ports):
            return "high"
        if len(open_ports) > 5:
            return "medium"
        if len(open_ports) > 0:
            return "low"
        return "minimal"

    # ------------------------------------------------------------------
    # Tools (callable directly via agent.tool_name(args))
    # ------------------------------------------------------------------

    def ping_host(self, host: str) -> Dict[str, Any]:
        """
        Check if a host is reachable via ping.

        Args:
            host: Target hostname or IP address.

        Returns:
            Dict with reachability result and response time.
        """
        try:
            result = subprocess.run(
                ["ping", "-c", "1", host],
                capture_output=True,
                text=True,
                timeout=10,
            )
            is_reachable = result.returncode == 0
            return {
                "host": host,
                "reachable": is_reachable,
                "response_time": self._extract_ping_time(result.stdout) if is_reachable else None,
                "timestamp": self._get_timestamp(),
            }
        except Exception as exc:
            return {
                "host": host,
                "reachable": False,
                "error": str(exc),
                "timestamp": self._get_timestamp(),
            }

    def scan_ports(
        self, host: str, ports: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Scan a list of TCP ports on a target host.

        Args:
            host: Target hostname or IP address.
            ports: Ports to scan; defaults to a common set if not provided.

        Returns:
            Dict with open/closed ports and scan metadata.
        """
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 8080, 8443]

        open_ports: List[int] = []
        closed_ports: List[int] = []

        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                if sock.connect_ex((host, port)) == 0:
                    open_ports.append(port)
                else:
                    closed_ports.append(port)
            except Exception:
                closed_ports.append(port)
            finally:
                sock.close()

        scan_result: Dict[str, Any] = {
            "host": host,
            "open_ports": open_ports,
            "closed_ports": closed_ports,
            "total_scanned": len(ports),
            "timestamp": self._get_timestamp(),
        }

        # Persist to in-memory history
        self._context["scan_history"].append(scan_result)
        return scan_result

    def get_scan_history(self) -> List[Dict[str, Any]]:
        """
        Return all scans performed in this session.

        Returns:
            List of previous scan results.
        """
        return list(self._context["scan_history"])

    def network_summary(self, host: str) -> Dict[str, Any]:
        """
        Perform a comprehensive network summary: ping + port scan.

        Args:
            host: Target hostname or IP address.

        Returns:
            Dict with combined ping and port scan results and a risk assessment.
        """
        ping_result = self.ping_host(host)

        port_scan: Optional[Dict[str, Any]] = None
        if ping_result["reachable"]:
            port_scan = self.scan_ports(host)

        return {
            "host": host,
            "ping_result": ping_result,
            "port_scan": port_scan,
            "summary": {
                "reachable": ping_result["reachable"],
                "open_ports_count": len(port_scan["open_ports"]) if port_scan else 0,
                "risk_level": self._assess_risk_level(port_scan),
            },
            "timestamp": self._get_timestamp(),
        }


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = NetworkScannerAgent()

    print("Scanning localhost...")
    result = agent.network_summary("127.0.0.1")
    print(json.dumps(result, indent=2))

    print("\nScan History:")
    history = agent.get_scan_history()
    print(json.dumps(history, indent=2))
