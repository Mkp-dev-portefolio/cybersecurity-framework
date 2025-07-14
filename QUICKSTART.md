# 🚀 Quickstart Guide - Build Your First Security Agent

Welcome to the Cybersecurity Framework! This guide will help you create your first security agent in just 10 minutes.

## 📋 Prerequisites

- Python 3.9+ installed
- Docker (optional, for full deployment)
- Basic understanding of Python

## 🏃‍♂️ Quick Setup (5 minutes)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Mkp-dev-portefolio/cybersecurity-framework.git
cd cybersecurity-framework

# Create virtual environment
python3 -m venv quickstart-env
source quickstart-env/bin/activate  # On Windows: quickstart-env\Scripts\activate

# Install minimal dependencies
pip install -r requirements-quickstart.txt
```

### Step 2: Environment Setup

```bash
# Copy environment template
cp .env.example .env.quickstart

# Edit the quickstart environment file
echo "AGENT_NAME=my-first-agent" >> .env.quickstart
echo "LOG_LEVEL=INFO" >> .env.quickstart
```

## 🤖 Create Your First Agent (5 minutes)

### Step 1: Use the Agent Template

We'll create a simple "Network Scanner" agent that demonstrates the framework's capabilities:

```bash
# Create your agent directory
mkdir -p agents/network_scanner
cd agents/network_scanner
```

### Step 2: Create the Agent Class

Create `network_scanner_agent.py`:

```python
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
```

### Step 3: Create Requirements File

Create `requirements-quickstart.txt`:

```txt
# Minimal dependencies for quickstart
asyncio-mqtt==0.16.1
pydantic==2.10.4
python-dotenv==1.0.1
click==8.1.7
rich==13.9.4
```

### Step 4: Create the Run Script

Create `run_quickstart.py`:

```python
#!/usr/bin/env python3
"""
Quickstart script for the Cybersecurity Framework
"""
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.network_scanner.network_scanner_agent import NetworkScannerAgent

def main():
    # Load environment
    load_dotenv('.env.quickstart')
    
    console = Console()
    
    # Welcome message
    console.print(Panel.fit(
        "🚀 Cybersecurity Framework - Quickstart Demo\n"
        "Your first security agent is ready!",
        style="bold green"
    ))
    
    # Create the agent
    agent = NetworkScannerAgent()
    
    # Interactive menu
    while True:
        console.print("\n" + "="*50)
        console.print("Choose an action:", style="bold cyan")
        console.print("1. Ping a host")
        console.print("2. Scan ports on a host")
        console.print("3. Full network summary")
        console.print("4. View scan history")
        console.print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            host = input("Enter hostname or IP address: ").strip()
            if host:
                console.print(f"\n🔍 Pinging {host}...")
                result = agent.tool_registry.get_tool("ping_host")(host)
                display_result(console, result)
        
        elif choice == '2':
            host = input("Enter hostname or IP address: ").strip()
            if host:
                console.print(f"\n🔍 Scanning ports on {host}...")
                result = agent.tool_registry.get_tool("scan_ports")(host)
                display_port_scan(console, result)
        
        elif choice == '3':
            host = input("Enter hostname or IP address: ").strip()
            if host:
                console.print(f"\n🔍 Performing network summary for {host}...")
                result = agent.tool_registry.get_tool("network_summary")(host)
                display_network_summary(console, result)
        
        elif choice == '4':
            console.print("\n📊 Scan History:")
            history = agent.tool_registry.get_tool("get_scan_history")()
            display_scan_history(console, history)
        
        elif choice == '5':
            console.print("\n👋 Thanks for trying the Cybersecurity Framework!", style="bold green")
            break
        
        else:
            console.print("❌ Invalid choice. Please try again.", style="bold red")

def display_result(console, result):
    """Display a simple result"""
    console.print(json.dumps(result, indent=2))

def display_port_scan(console, result):
    """Display port scan results in a table"""
    table = Table(title=f"Port Scan Results for {result['host']}")
    table.add_column("Status", style="cyan")
    table.add_column("Ports", style="magenta")
    table.add_column("Count", style="green")
    
    table.add_row("Open", ", ".join(map(str, result['open_ports'])), str(len(result['open_ports'])))
    table.add_row("Closed", f"{len(result['closed_ports'])} ports", str(len(result['closed_ports'])))
    
    console.print(table)

def display_network_summary(console, result):
    """Display network summary"""
    summary = result['summary']
    
    # Status panel
    status_color = "green" if summary['reachable'] else "red"
    status_text = "✅ Reachable" if summary['reachable'] else "❌ Not Reachable"
    
    console.print(Panel(
        f"Host: {result['host']}\n"
        f"Status: {status_text}\n"
        f"Open Ports: {summary['open_ports_count']}\n"
        f"Risk Level: {summary['risk_level'].upper()}",
        title="Network Summary",
        border_style=status_color
    ))

def display_scan_history(console, history):
    """Display scan history"""
    if not history:
        console.print("No scan history available.", style="yellow")
        return
    
    table = Table(title="Scan History")
    table.add_column("Host", style="cyan")
    table.add_column("Open Ports", style="green")
    table.add_column("Timestamp", style="blue")
    
    for scan in history:
        table.add_row(
            scan['host'],
            str(len(scan['open_ports'])),
            scan['timestamp'][:19]  # Truncate timestamp
        )
    
    console.print(table)

if __name__ == "__main__":
    main()
```

### Step 5: Create Environment Template

Create `.env.example`:

```env
# Quickstart Environment Configuration
AGENT_NAME=network-scanner
LOG_LEVEL=INFO
PYTHONPATH=.

# Optional: Add your own configuration
# API_KEY=your-api-key-here
# DATABASE_URL=sqlite:///quickstart.db
```

## 🎯 Run Your First Agent

```bash
# Make sure you're in the project root
cd /path/to/cybersecurity-framework

# Install quickstart dependencies
pip install -r requirements-quickstart.txt

# Run the quickstart demo
python run_quickstart.py
```

## 🎮 Try It Out

1. **Start the interactive demo**: `python run_quickstart.py`
2. **Choose option 1**: Ping a host (try `google.com` or `127.0.0.1`)
3. **Choose option 2**: Scan ports (try `127.0.0.1` for localhost)
4. **Choose option 3**: Get full network summary
5. **Choose option 4**: View your scan history

## 🧪 Expected Output

```
🚀 Cybersecurity Framework - Quickstart Demo
Your first security agent is ready!

==================================================
Choose an action:
1. Ping a host
2. Scan ports on a host
3. Full network summary
4. View scan history
5. Exit

Enter your choice (1-5): 3
Enter hostname or IP address: google.com

🔍 Performing network summary for google.com...

┌─ Network Summary ────────────────────────────────┐
│ Host: google.com                                 │
│ Status: ✅ Reachable                             │
│ Open Ports: 2                                   │
│ Risk Level: LOW                                  │
└──────────────────────────────────────────────────┘
```

## 🔧 Customize Your Agent

### Add New Tools

Edit `network_scanner_agent.py` and add new tools:

```python
@self.tool_registry.register_tool
def my_custom_tool(parameter: str) -> Dict[str, Any]:
    """
    Your custom security tool
    
    Args:
        parameter: Input parameter
        
    Returns:
        Dict with results
    """
    # Your custom logic here
    return {
        "result": f"Processed {parameter}",
        "timestamp": self._get_timestamp()
    }
```

### Extend Functionality

- **Add database storage**: Store scan results in SQLite
- **Add notifications**: Send alerts for high-risk findings
- **Add more protocols**: SNMP, SSH, FTP scanning
- **Add reporting**: Generate PDF reports of scans

## 🚀 Next Steps

Once you've successfully run your first agent:

1. **Read the full documentation**: Check out the main [README.md](README.md)
2. **Explore advanced agents**: Look at `agents/pki/pki_agent.py` for PKI management
3. **Set up the full infrastructure**: Use Docker Compose for complete deployment
4. **Integrate with MCP**: Connect your agent to the MCP server
5. **Build your own agents**: Create agents for your specific security needs

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running from the project root
2. **Permission errors**: Some network operations might require elevated privileges
3. **Timeout errors**: Increase timeout values for slow networks

### Get Help

- **Check the logs**: Enable debug logging with `LOG_LEVEL=DEBUG`
- **Read the documentation**: Full docs in [README.md](README.md)
- **Open an issue**: Report bugs on GitHub

## 📚 Learning Resources

- **Agent Architecture**: [agents/base/agent.py](agents/base/agent.py)
- **Tool System**: [agents/base/tool_registry.py](agents/base/tool_registry.py)
- **Memory System**: [agents/base/memory.py](agents/base/memory.py)
- **Full Framework**: [framework-structure.md](framework-structure.md)

---

**Congratulations! 🎉 You've just built and run your first security agent!**

This quickstart demonstrates the core concepts of the Cybersecurity Framework. You can now extend this agent or create entirely new ones for your specific security needs.

Ready to build the next generation of security automation? Let's go! 🚀
