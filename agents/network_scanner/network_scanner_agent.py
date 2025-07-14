from agents.base.agent import BaseAgent
from agents.base.memory import Memory
from agents.base.tool_registry import ToolRegistry
import socket
import subprocess
import json
from typing import Dict, List, Any

class NetworkScannerAgent(BaseAgent):
    """
    A simple network scanning agent that demonstrates the framework.
    
    This agent can:
    - Scan open ports on a target host
    - Check if a host is reachable
    - Perform basic network reconnaissance
    """
    
    def __init__(self, name: str = "NetworkScanner", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.description = "Network scanning and reconnaissance agent"
        self.version = "1.0.0"
        
        # Register tools
        self._register_tools()
        
        # Initialize memory for scan results
        self.memory.add_context("scan_history", [])
    
    def _register_tools(self):
        """Register all available tools for this agent"""
        
        @self.tool_registry.register_tool
        def ping_host(host: str) -> Dict[str, Any]:
            """
            Check if a host is reachable via ping
            
            Args:
                host: Target hostname or IP address
                
            Returns:
                Dict with ping results
            """
            try:
                # Use ping command (works on Unix/Linux/macOS)
                result = subprocess.run(
                    ['ping', '-c', '1', host], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                is_reachable = result.returncode == 0
                
                return {
                    "host": host,
                    "reachable": is_reachable,
                    "response_time": self._extract_ping_time(result.stdout) if is_reachable else None,
                    "timestamp": self._get_timestamp()
                }
                
            except Exception as e:
                return {
                    "host": host,
                    "reachable": False,
                    "error": str(e),
                    "timestamp": self._get_timestamp()
                }
        
        @self.tool_registry.register_tool
        def scan_ports(host: str, ports: List[int] = None) -> Dict[str, Any]:
            """
            Scan common ports on a target host
            
            Args:
                host: Target hostname or IP address
                ports: List of ports to scan (default: common ports)
                
            Returns:
                Dict with scan results
            """
            if ports is None:
                ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 8080, 8443]
            
            open_ports = []
            closed_ports = []
            
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                
                try:
                    result = sock.connect_ex((host, port))
                    if result == 0:
                        open_ports.append(port)
                    else:
                        closed_ports.append(port)
                except Exception:
                    closed_ports.append(port)
                finally:
                    sock.close()
            
            scan_result = {
                "host": host,
                "open_ports": open_ports,
                "closed_ports": closed_ports,
                "total_scanned": len(ports),
                "timestamp": self._get_timestamp()
            }
            
            # Store in memory
            scan_history = self.memory.get_context("scan_history")
            scan_history.append(scan_result)
            self.memory.add_context("scan_history", scan_history)
            
            return scan_result
        
        @self.tool_registry.register_tool
        def get_scan_history() -> List[Dict[str, Any]]:
            """
            Get the history of all scans performed
            
            Returns:
                List of previous scan results
            """
            return self.memory.get_context("scan_history")
        
        @self.tool_registry.register_tool
        def network_summary(host: str) -> Dict[str, Any]:
            """
            Perform a comprehensive network summary of a host
            
            Args:
                host: Target hostname or IP address
                
            Returns:
                Dict with comprehensive network information
            """
            # Ping the host
            ping_result = ping_host(host)
            
            # Scan ports if host is reachable
            port_scan = None
            if ping_result["reachable"]:
                port_scan = scan_ports(host)
            
            return {
                "host": host,
                "ping_result": ping_result,
                "port_scan": port_scan,
                "summary": {
                    "reachable": ping_result["reachable"],
                    "open_ports_count": len(port_scan["open_ports"]) if port_scan else 0,
                    "risk_level": self._assess_risk_level(port_scan) if port_scan else "unknown"
                },
                "timestamp": self._get_timestamp()
            }
    
    def _extract_ping_time(self, ping_output: str) -> str:
        """Extract ping time from ping command output"""
        lines = ping_output.split('\n')
        for line in lines:
            if 'time=' in line:
                return line.split('time=')[1].split()[0]
        return "unknown"
    
    def _assess_risk_level(self, port_scan: Dict[str, Any]) -> str:
        """Assess risk level based on open ports"""
        if not port_scan:
            return "unknown"
            
        open_ports = port_scan["open_ports"]
        
        # High risk ports
        high_risk_ports = [21, 23, 135, 139, 445, 1433, 3389]
        
        if any(port in open_ports for port in high_risk_ports):
            return "high"
        elif len(open_ports) > 5:
            return "medium"
        elif len(open_ports) > 0:
            return "low"
        else:
            return "minimal"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

# Example usage
if __name__ == "__main__":
    # Create the agent
    agent = NetworkScannerAgent()
    
    # Example: Scan localhost
    print("🔍 Scanning localhost...")
    result = agent.tool_registry.get_tool("network_summary")("127.0.0.1")
    print(json.dumps(result, indent=2))
    
    # Example: Get scan history
    print("\n📊 Scan History:")
    history = agent.tool_registry.get_tool("get_scan_history")()
    print(json.dumps(history, indent=2))
